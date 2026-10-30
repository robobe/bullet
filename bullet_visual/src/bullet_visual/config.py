"""Strict YAML configuration for visual capture and publication."""
from dataclasses import dataclass
from pathlib import Path

import yaml
from bullet_msgs import validate_endpoint


@dataclass(frozen=True)
class SourceConfig:
    type: str
    endpoint: str | None = None
    topic: str = 'camera/front/image'
    device: int | str | None = None
    pipeline: str | None = None

    def __post_init__(self):
        if self.type not in ('zmq_shm', 'usb', 'mipi'):
            raise ValueError('source.type must be zmq_shm, usb, or mipi')
        if self.type == 'zmq_shm' and (not isinstance(self.endpoint, str) or not self.endpoint):
            raise ValueError('source.endpoint is required for zmq_shm')
        if self.type == 'zmq_shm':
            validate_endpoint(self.endpoint)
        if self.type == 'usb' and self.device is None:
            raise ValueError('source.device is required for usb')
        if self.type == 'mipi' and (not isinstance(self.pipeline, str) or not self.pipeline.strip()):
            raise ValueError('source.pipeline is required for mipi')
        if not isinstance(self.topic, str) or not self.topic or '\0' in self.topic:
            raise ValueError('source.topic must be a nonempty string')


@dataclass(frozen=True)
class OutputConfig:
    endpoint: str = 'tcp://127.0.0.1:5560'
    image_topic: str = 'camera/front/image'

    def __post_init__(self):
        if not isinstance(self.endpoint, str) or not self.endpoint:
            raise ValueError('output.endpoint must be a nonempty string')
        validate_endpoint(self.endpoint)
        if not isinstance(self.image_topic, str) or not self.image_topic:
            raise ValueError('output.image_topic must be a nonempty string')


@dataclass(frozen=True)
class VisualConfig:
    source: SourceConfig
    output: OutputConfig


def _mapping(value, name, fields):
    if not isinstance(value, dict) or set(value) - set(fields):
        raise ValueError(f'invalid {name} fields')
    return value


def load_config(path: str | Path) -> VisualConfig:
    try:
        data = yaml.safe_load(Path(path).read_text())
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ValueError('invalid visual configuration') from error
    root = _mapping(data, 'visual configuration', ('source', 'output'))
    source_data = _mapping(root.get('source'), 'source', ('type', 'endpoint', 'topic', 'device', 'pipeline'))
    output_data = _mapping(root.get('output'), 'output', ('endpoint', 'image_topic'))
    source = SourceConfig(**source_data)
    output = OutputConfig(**output_data)
    if source.type == 'zmq_shm' and source.endpoint == output.endpoint:
        raise ValueError('source.endpoint and output.endpoint must differ')
    return VisualConfig(source, output)
