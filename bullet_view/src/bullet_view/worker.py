"""Receive-only MAVLink worker; no GUI or reconnect policy belongs here."""
from threading import Event
import time

from PySide6 import QtCore
from pymavlink import mavutil

from .model import Attitude, Altitude, TelemetryUpdate


RECEIVE_TIMEOUT_S = .2


class MavlinkWorker(QtCore.QObject):
    update = QtCore.Signal(object)
    connected = QtCore.Signal()
    failed = QtCore.Signal(str)
    finished = QtCore.Signal()

    def __init__(self, endpoint, *, connection_factory=mavutil.mavlink_connection, clock=time.monotonic):
        super().__init__()
        self.endpoint = endpoint
        self.connection_factory = connection_factory
        self.clock = clock
        self.stop_requested = Event()
        self.connection = None

    def request_stop(self):
        self.stop_requested.set()

    @QtCore.Slot()
    def run(self):
        try:
            self.connection = self.connection_factory(self.endpoint)
            self.connected.emit()
            while not self.stop_requested.is_set():
                message = self.connection.recv_match(
                    type=['HEARTBEAT', 'ATTITUDE', 'ALTITUDE'],
                    blocking=True,
                    timeout=RECEIVE_TIMEOUT_S,
                )
                if message is not None:
                    self._emit_message(message, self.clock())
        except Exception as error:
            if not self.stop_requested.is_set():
                self.failed.emit(str(error))
        finally:
            if self.connection is not None:
                self.connection.close()
            self.finished.emit()

    def _emit_message(self, message, received_at_s):
        kind = message.get_type()
        if kind == 'HEARTBEAT':
            value = None
        elif kind == 'ATTITUDE':
            value = Attitude(message.roll, message.pitch, message.yaw, message.time_boot_ms)
        elif kind == 'ALTITUDE':
            value = Altitude(message.altitude_local, message.time_usec)
        else:
            return
        self.update.emit(TelemetryUpdate(kind, value, received_at_s))
