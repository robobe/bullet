"""Bullet Visual application entry point."""
import sys

from loguru import logger

from .cli import CliParser
from .config import load_config
from .runtime import VisualRuntime


def configure_logging():
    logger.remove()
    logger.add(sys.stdout, format='{message}')


def main(argv=None):
    configure_logging()
    try:
        options = CliParser().parse(argv)
        config = load_config(options.config)
        VisualRuntime(config).run()
        return 0
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
