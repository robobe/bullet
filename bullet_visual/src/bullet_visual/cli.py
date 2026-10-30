"""Click CLI parsing without starting capture or detector workers."""
from dataclasses import dataclass
from pathlib import Path

import click


@dataclass(frozen=True)
class AppOptions:
    config: Path


@click.command()
@click.option('--config', type=click.Path(path_type=Path), required=True,
              help='YAML source/output configuration')
def command(config):
    return AppOptions(config)


class CliParser:
    def parse(self, argv=None):
        return command.main(args=argv, standalone_mode=False)
