"""Receive-only MAVLink worker; no GUI or reconnect policy belongs here."""
from threading import Event
import time
from math import isfinite

from PySide6 import QtCore
from pymavlink import mavutil
import re

from .model import Attitude, Altitude, Bbox, Heartbeat, StatusText, TelemetryUpdate


RECEIVE_TIMEOUT_S = .2
STATUS_INDEX_RE = re.compile(r'^\[(\d+)\]\s*(.*)$')
BBOX_NAMES = {'BBOX_VALID', 'BBOX_X', 'BBOX_Y', 'BBOX_W', 'BBOX_H'}


class MavlinkWorker(QtCore.QObject):
    update = QtCore.Signal(object)
    connected = QtCore.Signal()
    failed = QtCore.Signal(str)
    finished = QtCore.Signal()
    command_result = QtCore.Signal(str)

    def __init__(self, endpoint, *, control_endpoint=None,
                 connection_factory=mavutil.mavlink_connection, clock=time.monotonic):
        super().__init__()
        self.endpoint = endpoint
        self.connection_factory = connection_factory
        self.control_endpoint = control_endpoint
        self.clock = clock
        self.stop_requested = Event()
        self.connection = None
        self.control_connection = None
        self.reload_requested = Event()
        self.bbox_values = {}

    def request_stop(self):
        self.stop_requested.set()

    def request_reload(self):
        self.reload_requested.set()

    @QtCore.Slot()
    def run(self):
        try:
            self.connection = self.connection_factory(self.endpoint)
            if self.control_endpoint is not None:
                self.control_connection = self.connection_factory(self.control_endpoint)
            self.connected.emit()
            while not self.stop_requested.is_set():
                if self.control_connection is not None and self.reload_requested.is_set():
                    self.control_connection.mav.command_long_send(
                        1, 1, 31010, 0, 1.0, 0., 0., 0., 0., 0., 0.)
                    self.reload_requested.clear()
                if self.control_connection is not None:
                    ack = self.control_connection.recv_match(type='COMMAND_ACK', blocking=False)
                    if ack is not None:
                        self.command_result.emit(f'Reload command result: {ack.result}')
                message = self.connection.recv_match(
                type=['HEARTBEAT', 'ATTITUDE', 'ALTITUDE', 'STATUSTEXT', 'NAMED_VALUE_FLOAT'],
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
            if self.control_connection is not None:
                self.control_connection.close()
            self.finished.emit()

    def _emit_message(self, message, received_at_s):
        kind = message.get_type()
        if kind == 'HEARTBEAT':
            value = Heartbeat(getattr(message, 'base_mode', 0),
                              getattr(message, 'system_status', 0), received_at_s)
        elif kind == 'ATTITUDE':
            value = Attitude(message.roll, message.pitch, message.yaw, message.time_boot_ms)
        elif kind == 'ALTITUDE':
            value = Altitude(message.altitude_local, message.time_usec)
        elif kind == 'STATUSTEXT':
            raw_text = message.text.decode('utf-8', errors='replace') if isinstance(message.text, bytes) else message.text
            match = STATUS_INDEX_RE.match(raw_text)
            index = int(match.group(1)) if match else 0
            value = StatusText(index, message.severity, raw_text, received_at_s)
        elif kind == 'NAMED_VALUE_FLOAT':
            raw_name = message.name.decode('ascii', errors='ignore') if isinstance(message.name, bytes) else message.name
            name = str(raw_name).rstrip('\0')
            if name not in BBOX_NAMES:
                return
            self.bbox_values[name] = float(message.value)
            valid = self.bbox_values.get('BBOX_VALID', 0.) > .5
            coordinates = tuple(self.bbox_values.get(name) for name in ('BBOX_X', 'BBOX_Y', 'BBOX_W', 'BBOX_H'))
            value = Bbox(valid, *coordinates) if valid and all(
                item is not None and isfinite(item) for item in coordinates
            ) else Bbox(False)
            kind = 'BBOX'
        else:
            return
        self.update.emit(TelemetryUpdate(kind, value, received_at_s))
