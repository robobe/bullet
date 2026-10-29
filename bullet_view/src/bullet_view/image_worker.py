"""Local ZMQ descriptor and SHM image worker for Bullet View."""
from threading import Event

from PySide6 import QtCore
import zmq

from bullet_msgs.shm import FrameReader, MAX_MESSAGE_BYTES, topic_prefix

from .model import ImageFrame


POLL_TIMEOUT_MS = 50


class LocalImageWorker(QtCore.QObject):
    frame = QtCore.Signal(object)
    failed = QtCore.Signal(str)
    finished = QtCore.Signal()

    def __init__(self, endpoint, topic):
        super().__init__()
        self.endpoint = endpoint
        self.topic = topic
        self.stop_requested = Event()
        self.reader = None
        self.context = None
        self.socket = None

    def request_stop(self):
        self.stop_requested.set()

    @QtCore.Slot()
    def run(self):
        try:
            self.reader = FrameReader(self.topic)
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.SUB)
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.setsockopt(zmq.CONFLATE, 1)
            self.socket.setsockopt(zmq.MAXMSGSIZE, MAX_MESSAGE_BYTES)
            self.socket.setsockopt(zmq.SUBSCRIBE, topic_prefix(self.topic))
            self.socket.connect(self.endpoint)
            while not self.stop_requested.is_set():
                if not self.socket.poll(POLL_TIMEOUT_MS):
                    continue
                message = self.socket.recv()
                if self.socket.getsockopt(zmq.RCVMORE):
                    raise ValueError('expected one image descriptor message')
                result = self.reader.read(message)
                if result is None:
                    continue
                metadata, pixels = result
                row_bytes = metadata['width'] * 3
                packed = b''.join(
                    pixels[offset:offset + row_bytes]
                    for offset in range(0, metadata['step'] * metadata['height'], metadata['step'])
                )
                self.frame.emit(ImageFrame(metadata['width'], metadata['height'], metadata['encoding'],
                                           packed, metadata['sequence'], metadata['capture_ns']))
        except Exception as error:
            if not self.stop_requested.is_set():
                self.failed.emit(str(error))
        finally:
            if self.reader is not None:
                self.reader.close()
            if self.socket is not None:
                self.socket.close(linger=0)
            if self.context is not None:
                self.context.term()
            self.finished.emit()
