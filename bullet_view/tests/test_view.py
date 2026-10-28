import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PySide6 import QtCore, QtWidgets

from bullet_view.model import Altitude, Attitude, TelemetrySnapshot
from bullet_view.view import MainWindow


class FakePresenter(QtCore.QObject):
    snapshot_changed = QtCore.Signal(object)
    status_changed = QtCore.Signal(str)
    endpoint = 'udpin:0.0.0.0:14550'

    def stop(self):
        pass


@pytest.fixture
def application():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_view_has_telemetry_and_parameters_tabs_and_renders_snapshot(application):
    presenter = FakePresenter()
    window = MainWindow(presenter)
    try:
        snapshot = TelemetrySnapshot(attitude=Attitude(.1, .2, .3, 10), altitude=Altitude(4., 20))
        window.set_snapshot(snapshot)
        assert window.tabs.count() == 2
        assert window.tabs.tabText(0) == 'Telemetry'
        assert window.tabs.tabText(1) == 'Parameters'
        assert '+17.2°' in window.yaw.text()
        assert window.altitude.altitude_m == 4.
    finally:
        window.close()
