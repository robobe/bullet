import json
from types import SimpleNamespace

import pytest

from bullet_visual.publisher import BboxPublisher


def test_publisher_builds_v1_packet_without_network(monkeypatch, tmp_path):
    sent = []
    publisher = BboxPublisher.__new__(BboxPublisher)
    publisher.validator = SimpleNamespace(validate=lambda packet: sent.append(packet))
    publisher.socket = SimpleNamespace(send_multipart=lambda parts, flags: None)

    metadata = {'version': 1, 'session': 'a' * 32, 'sequence': 1, 'capture_ns': 123}
    assert publisher.publish(metadata, (1, 2, 3, 4), 'camera/front/image')
    assert sent[0]['schema_version'] == 1
    assert sent[0]['bbox'] == {'x': 1, 'y': 2, 'width': 3, 'height': 4}
