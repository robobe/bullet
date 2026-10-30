"""Two-thread latest-frame capture, detection, and publication runtime."""
from collections import Counter
from threading import Condition, Event, Thread
import time

from bullet_perception import detect_bbox
from loguru import logger

from .capture import Frame, open_source
from .config import VisualConfig
from .publisher import BboxPublisher


class LatestFrame:
    def __init__(self):
        self.condition = Condition()
        self.frame = None
        self.closed = False

    def put(self, frame: Frame):
        with self.condition:
            self.frame = frame
            self.condition.notify()

    def take(self, stop: Event):
        with self.condition:
            while self.frame is None and not self.closed and not stop.is_set():
                self.condition.wait(.05)
            frame, self.frame = self.frame, None
            return frame

    def close(self):
        with self.condition:
            self.closed = True
            self.condition.notify_all()


class VisualRuntime:
    def __init__(self, config: VisualConfig):
        self.config = config
        self.stop = Event()
        self.slot = LatestFrame()
        self.source = None
        self.publisher = None
        self.error = None
        self.counters = Counter()

    def run(self):
        capture = detect = None
        try:
            self.source = open_source(self.config.source)
            self.publisher = BboxPublisher(self.config.output.endpoint)
            capture = Thread(name='bullet-visual-capture', target=self._capture, daemon=True)
            detect = Thread(name='bullet-visual-detect', target=self._detect, daemon=True)
            capture.start()
            detect.start()
            while not self.stop.wait(1.):
                logger.info('Visual source={} captured={} processed={} dropped={} no_target={} publish_drops={}',
                            self.config.source.type, self.counters['captured'], self.counters['processed'],
                            self.counters['dropped'], self.counters['no_target'], self.counters['publish_drops'])
        finally:
            self.stop.set()
            self.slot.close()
            if capture is not None:
                capture.join(2.)
            if detect is not None:
                detect.join(2.)
            if self.source is not None:
                self.source.close()
            if self.publisher is not None:
                self.publisher.close()
        if self.error is not None:
            raise self.error

    def _capture(self):
        try:
            while not self.stop.is_set():
                frame = self.source.poll()
                if frame is None:
                    self.stop.wait(.002)
                    continue
                self.counters['captured'] += 1
                with self.slot.condition:
                    if self.slot.frame is not None:
                        self.counters['dropped'] += 1
                self.slot.put(frame)
        except BaseException as error:
            self.error = error
            self.stop.set()
            self.slot.close()

    def _detect(self):
        try:
            while not self.stop.is_set():
                frame = self.slot.take(self.stop)
                if frame is None:
                    continue
                bbox = detect_bbox(frame.image)
                self.counters['processed'] += 1
                if bbox is None:
                    self.counters['no_target'] += 1
                if not self.publisher.publish(frame.metadata, bbox, self.config.output.image_topic):
                    self.counters['publish_drops'] += 1
        except BaseException as error:
            self.error = error
            self.stop.set()
