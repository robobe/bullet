"""Bullet View application entry point."""
import argparse
import sys

from PySide6 import QtWidgets

from .presenter import Presenter
from .view import MainWindow


DEFAULT_ENDPOINT = 'udpin:0.0.0.0:14550'


def main(argv=None):
    parser = argparse.ArgumentParser(description='Bullet View MAVLink telemetry viewer')
    parser.add_argument('--mavlink-endpoint', default=DEFAULT_ENDPOINT,
                        help='pymavlink input connection string')
    parser.add_argument('--mavlink-control-endpoint', default='udpout:127.0.0.1:14551',
                        help='pymavlink control output for profile reload')
    args = parser.parse_args(argv)
    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    presenter = Presenter(args.mavlink_endpoint, control_endpoint=args.mavlink_control_endpoint)
    window = MainWindow(presenter)
    window.show()
    presenter.start()
    return application.exec()


if __name__ == '__main__':
    raise SystemExit(main())
