"""MVP presenter connecting MAVLink updates to the view."""
from dataclasses import replace
import time

from PySide6 import QtCore

from .model import TelemetrySnapshot
from .worker import MavlinkWorker


STALE_AFTER_S = .75
VIEW_REFRESH_PERIOD_MS = 100


class Presenter(QtCore.QObject):
    snapshot_changed = QtCore.Signal(object)
    status_changed = QtCore.Signal(str)

    def __init__(self, endpoint, *, worker_factory=MavlinkWorker, clock=time.monotonic):
        super().__init__()
        self.endpoint = endpoint
        self.worker_factory = worker_factory
        self.clock = clock
        self.snapshot = TelemetrySnapshot()
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
        self.snapshot = replace(self.snapshot, **values)
        if first_message:
            self._set_status('Connected')
        self.snapshot_changed.emit(self.snapshot)

    @QtCore.Slot(str)
    def _on_failure(self, message):
        self.snapshot = replace(self.snapshot, connected=False, error=message)
        self._set_status('Disconnected: ' + message)
        self.snapshot_changed.emit(self.snapshot)

    def _refresh_freshness(self):
        if self.snapshot.last_message_at_s is None:
            return
        age = self.clock() - self.snapshot.last_message_at_s
        if age > STALE_AFTER_S and self.snapshot.connected:
            self.snapshot = replace(self.snapshot, connected=False)
            self._set_status('Telemetry stale')
            self.snapshot_changed.emit(self.snapshot)

    def _set_status(self, message):
        self.status_changed.emit(message)
