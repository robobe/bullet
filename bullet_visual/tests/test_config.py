import pytest

from bullet_visual.config import load_config


def test_load_zmq_config(tmp_path):
    path = tmp_path / 'visual.yaml'
    path.write_text('''
source:
  type: zmq_shm
  endpoint: tcp://127.0.0.1:5556
  topic: camera/front/image
output:
  endpoint: tcp://127.0.0.1:5560
  image_topic: camera/front/image
''')
    config = load_config(path)
    assert config.source.type == 'zmq_shm'
    assert config.output.endpoint.endswith(':5560')


@pytest.mark.parametrize('source', [
    {'type': 'usb'},
    {'type': 'mipi'},
    {'type': 'other'},
])
def test_reject_invalid_source(source, tmp_path):
    path = tmp_path / 'visual.yaml'
    path.write_text(f'source: {source!r}\noutput: {{}}\n')
    with pytest.raises(ValueError):
        load_config(path)


def test_reject_unknown_fields(tmp_path):
    path = tmp_path / 'visual.yaml'
    path.write_text('source: {type: usb, device: 0, extra: true}\noutput: {}\n')
    with pytest.raises(ValueError):
        load_config(path)


def test_reject_source_output_endpoint_collision(tmp_path):
    path = tmp_path / 'visual.yaml'
    path.write_text('''
source: {type: zmq_shm, endpoint: tcp://127.0.0.1:5559}
output: {endpoint: tcp://127.0.0.1:5559}
''')
    with pytest.raises(ValueError, match='must differ'):
        load_config(path)
