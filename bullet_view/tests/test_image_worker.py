from unittest.mock import Mock

import pytest

from bullet_view import image_worker


@pytest.mark.parametrize('simulation_time', [None, 0., 12.345])
def test_image_worker_retains_optional_simulation_time(monkeypatch, simulation_time):
    worker = image_worker.LocalImageWorker('test', 'camera/front/image')
    metadata = dict(width=2, height=2, step=6, encoding='rgb8', sequence=42, capture_ns=1000)
    if simulation_time is not None:
        metadata['source'] = {'simulation_time_s': simulation_time}
    reader = Mock()
    reader.read.return_value = (metadata, bytes(12))
    monkeypatch.setattr(image_worker, 'FrameReader', lambda topic: reader)
    context = Mock()
    socket = context.socket.return_value
    socket.poll.return_value = True
    socket.getsockopt.return_value = False
    monkeypatch.setattr(image_worker.zmq, 'Context', lambda: context)
    frames = []
    errors = []
    worker.frame.connect(frames.append)
    worker.frame.connect(lambda frame: worker.request_stop())
    worker.failed.connect(errors.append)

    worker.run()

    assert not errors
    assert len(frames) == 1
    assert frames[0].simulation_time_s == simulation_time
    assert frames[0].sequence == 42
    assert frames[0].pixels == bytes(12)
    reader.close.assert_called_once()
