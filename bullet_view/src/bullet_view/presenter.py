"""MVP presenter connecting MAVLink updates to the view."""
from dataclasses import replace
import time

from PySide6 import QtCore

from .model import TelemetrySnapshot
from .worker import MavlinkWorker


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

    def __init__(self, endpoint, *, worker_factory=MavlinkWorker, clock=time.monotonic):
        super().__init__()
        self.endpoint = endpoint
        self.worker_factory = worker_factory
        self.clock = clock
        self.snapshot = TelemetrySnapshot()
        self.vertical_speed = VerticalSpeedEstimator()
        self.thread = QtCore.QThread(self)
        self.worker = worker_factory(endpoint)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.update.connect(self._on_update)
        self.worker.connected.connect(lambda: self._set_status('Listening for MAVLink telemetry'))
        self.worker.failed.connect(self._on_failure)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(VIEW_REFRESH_PERIOD_MS)
        self.timer.timeout.connect(self._refresh_freshness)

    def start(self):
        self.thread.start()
        self.timer.start()

    def stop(self):
        self.timer.stop()
        self.worker.request_stop()
        if self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(2000)

    @QtCore.Slot(object)
    def _on_update(self, update):
        first_message = not self.snapshot.connected
        values = dict(connected=True, last_message_at_s=update.received_at_s,
                      error=None)
        if update.kind == 'HEARTBEAT':
            values['heartbeat_at_s'] = update.received_at_s
        elif update.kind == 'ATTITUDE':
            values['attitude'] = update.value
        elif update.kind == 'ALTITUDE':
            values['altitude'] = update.value
            values['vertical_speed_m_s'] = self.vertical_speed.update(
                update.value.local_m, update.received_at_s)
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
