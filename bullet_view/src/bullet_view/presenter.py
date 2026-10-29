"""MVP presenter connecting MAVLink updates to the view."""
from dataclasses import replace
import time

from PySide6 import QtCore
from pymavlink import mavutil

from .model import TelemetrySnapshot
from .worker import MavlinkWorker
from .image_worker import LocalImageWorker


STALE_AFTER_S = .75
VIEW_REFRESH_PERIOD_MS = 100
VERTICAL_SPEED_FILTER_ALPHA = .25
VERTICAL_SPEED_RESET_GAP_S = 1.


class VerticalSpeedEstimator:
    def __init__(self, *, alpha=VERTICAL_SPEED_FILTER_ALPHA, reset_gap_s=VERTICAL_SPEED_RESET_GAP_S):
        self.alpha = alpha
        self.reset_gap_s = reset_gap_s
        self.previous_altitude_m = None
        self.previous_received_at_s = None
        self.filtered_speed_m_s = None

    def reset(self):
        self.previous_altitude_m = None
        self.previous_received_at_s = None
        self.filtered_speed_m_s = None

    def update(self, altitude_m, received_at_s):
        previous_altitude_m = self.previous_altitude_m
        previous_received_at_s = self.previous_received_at_s
        self.previous_altitude_m = altitude_m
        self.previous_received_at_s = received_at_s
        if previous_altitude_m is None or previous_received_at_s is None:
            self.filtered_speed_m_s = None
            return None
        delta_s = received_at_s - previous_received_at_s
        if delta_s <= 0 or delta_s > self.reset_gap_s:
            self.filtered_speed_m_s = None
            return None
        raw_speed_m_s = (altitude_m - previous_altitude_m) / delta_s
        if self.filtered_speed_m_s is None:
            self.filtered_speed_m_s = raw_speed_m_s
        else:
            self.filtered_speed_m_s += self.alpha * (raw_speed_m_s - self.filtered_speed_m_s)
        return self.filtered_speed_m_s


class Presenter(QtCore.QObject):
    snapshot_changed = QtCore.Signal(object)
    status_changed = QtCore.Signal(str)

    def __init__(self, endpoint, *, control_endpoint='udpout:127.0.0.1:14551',
                 image_endpoint='tcp://127.0.0.1:5556', image_topic='camera/front/image',
                 image_mode='remote', worker_factory=MavlinkWorker, clock=time.monotonic):
        super().__init__()
        self.endpoint = endpoint
        self.control_endpoint = control_endpoint
        self.worker_factory = worker_factory
        self.clock = clock
        self.image_endpoint = image_endpoint
        self.image_topic = image_topic
        self.image_mode = image_mode
        self.snapshot = TelemetrySnapshot()
        self.vertical_speed = VerticalSpeedEstimator()
        self.thread = QtCore.QThread(self)
        self.worker = worker_factory(endpoint, control_endpoint=control_endpoint)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.update.connect(self._on_update)
        self.worker.connected.connect(lambda: self._set_status('Listening for MAVLink telemetry'))
        self.worker.failed.connect(self._on_failure)
        self.worker.command_result.connect(self._set_status)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(VIEW_REFRESH_PERIOD_MS)
        self.timer.timeout.connect(self._refresh_freshness)
        self.image_thread = None
        self.image_worker = None

    def start(self):
        self.thread.start()
        if self.image_mode == 'local':
            self._start_image_worker()
        self.timer.start()

    def stop(self):
        self.timer.stop()
        self.worker.request_stop()
        if self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(2000)
        self._stop_image_worker()

    def set_image_mode(self, mode):
        if mode not in ('local', 'remote') or mode == self.image_mode:
            return
        self.image_mode = mode
        if mode == 'local':
            self._start_image_worker()
        else:
            self._stop_image_worker()
            self.snapshot = replace(self.snapshot, image=None)
            self.snapshot_changed.emit(self.snapshot)

    def _start_image_worker(self):
        if self.image_thread is not None and self.image_thread.isRunning():
            return
        self.image_thread = QtCore.QThread(self)
        self.image_worker = LocalImageWorker(self.image_endpoint, self.image_topic)
        self.image_worker.moveToThread(self.image_thread)
        self.image_thread.started.connect(self.image_worker.run)
        self.image_worker.frame.connect(self._on_frame)
        self.image_worker.failed.connect(lambda message: self._set_status('Image: ' + message))
        self.image_worker.finished.connect(self.image_thread.quit)
        self.image_thread.finished.connect(self.image_worker.deleteLater)
        self.image_thread.start()

    def _stop_image_worker(self):
        if self.image_worker is not None:
            self.image_worker.request_stop()
        if self.image_thread is not None and self.image_thread.isRunning():
            self.image_thread.quit()
            self.image_thread.wait(2000)
        self.image_worker = None
        self.image_thread = None

    @QtCore.Slot(object)
    def _on_frame(self, frame):
        self.snapshot = replace(self.snapshot, image=frame)
        self.snapshot_changed.emit(self.snapshot)

    def request_reload(self):
        if self.snapshot.mission_stopped:
            self.worker.request_reload()
        else:
            self._set_status('Profile reload requires stopped mission')

    @QtCore.Slot(object)
    def _on_update(self, update):
        first_message = not self.snapshot.connected
        values = dict(connected=True, last_message_at_s=update.received_at_s,
                      error=None)
        if update.kind == 'HEARTBEAT':
            values['heartbeat_at_s'] = update.received_at_s
            values['heartbeat'] = update.value
            values['mission_stopped'] = (update.value is not None
                                          and update.value.system_status != mavutil.mavlink.MAV_STATE_ACTIVE)
        elif update.kind == 'ATTITUDE':
            values['attitude'] = update.value
        elif update.kind == 'ALTITUDE':
            values['altitude'] = update.value
            values['vertical_speed_m_s'] = self.vertical_speed.update(
                update.value.local_m, update.received_at_s)
        elif update.kind == 'STATUSTEXT':
            values['messages'] = self.snapshot.messages + (update.value,)
        elif update.kind == 'BBOX':
            values['bbox'] = update.value
        self.snapshot = replace(self.snapshot, **values)
        if first_message:
            self._set_status('Connected')
        self.snapshot_changed.emit(self.snapshot)

    @QtCore.Slot(str)
    def _on_failure(self, message):
        self.vertical_speed.reset()
        self.snapshot = replace(self.snapshot, connected=False, error=message)
        self._set_status('Disconnected: ' + message)
        self.snapshot_changed.emit(self.snapshot)

    def _refresh_freshness(self):
        if self.snapshot.last_message_at_s is None:
            return
        age = self.clock() - self.snapshot.last_message_at_s
        if age > STALE_AFTER_S and self.snapshot.connected:
            self.vertical_speed.reset()
            self.snapshot = replace(self.snapshot, connected=False, vertical_speed_m_s=None)
            self._set_status('Telemetry stale')
            self.snapshot_changed.emit(self.snapshot)

    def _set_status(self, message):
        self.status_changed.emit(message)
