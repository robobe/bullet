"""Schema-validating, bounded bbox publisher."""
import json

import zmq
from bullet_msgs import schema_bytes, validate_endpoint
from bullet_msgs.flight import validate_source
from jsonschema import Draft202012Validator


BBOX_TOPIC = b'tracking/front/bbox'


class BboxPublisher:
    def __init__(self, endpoint):
        validate_endpoint(endpoint)
        self.validator = Draft202012Validator(json.loads(schema_bytes('bbox.json')))
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt(zmq.SNDHWM, 64)
        self.socket.bind(endpoint)

    def publish(self, metadata, bbox, image_topic):
        packet = {
            'schema_version': 1,
            'image_topic': image_topic,
            'session': metadata['session'],
            'sequence': metadata['sequence'],
            'capture_ns': metadata['capture_ns'],
            'bbox': None if bbox is None else dict(zip(('x', 'y', 'width', 'height'), bbox, strict=True)),
        }
        if metadata.get('version') == 2:
            source = validate_source(metadata.get('source'))
            if metadata['capture_ns'] != source['measurement_us'] * 1000:
                raise ValueError('bbox source/capture timestamp mismatch')
            packet.update(schema_version=2, source=source)
        self.validator.validate(packet)
        try:
            self.socket.send_multipart([BBOX_TOPIC, json.dumps(packet, separators=(',', ':')).encode()], flags=zmq.NOBLOCK)
        except zmq.Again:
            return False
        return True

    def close(self):
        self.socket.close(linger=0)
        self.context.term()
