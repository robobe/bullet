import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PySide6 import QtCore, QtWidgets

from bullet_view.model import Altitude, Attitude, Bbox, ImageFrame, StatusText, TelemetrySnapshot
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
        snapshot = TelemetrySnapshot(attitude=Attitude(.1, .2, .3, 10), altitude=Altitude(4., 20),
                                     vertical_speed_m_s=1.25,
                                     image=ImageFrame(2, 2, 'rgb8', bytes(12), 1, 2),
                                     bbox=Bbox(True, 0., 0., 1., 1.),
                                     messages=(StatusText(1, 6, '[01] ready', 1.),))
        window.set_snapshot(snapshot)
        assert window.tabs.count() == 2
        assert window.tabs.tabText(0) == 'Telemetry'
        assert window.tabs.tabText(1) == 'Parameters'
        assert '+17.2°' in window.yaw.text()
        assert window.altitude.altitude_m == 4.
        assert window.vertical_speed.vertical_speed_m_s == 1.25
        assert window.camera_frame.image is not None
        assert window.camera_frame.bbox == Bbox(True, 0., 0., 1., 1.)
        assert window.image_mode.currentText() == 'Local'
        assert window.roll.parentWidget().objectName() == 'attitude_summary'
        assert window.message_log.parentWidget().objectName() == 'status_panel'
        assert window.message_log.count() == 1
        assert window.message_log.item(0).text() == '[01] ready'
        window.message_log.itemClicked.emit(window.message_log.item(0))
        assert 'waiting for the application to report readiness' in window.message_details.text()
    finally:
        window.close()


def test_view_stops_auto_follow_after_completion(application):
    presenter = FakePresenter()
    window = MainWindow(presenter)
    try:
        messages = tuple(StatusText(index, 6, text, float(index)) for index, text in (
            (1, '[01] ready'), (30, '[30] mission completed'), (2, '[02] late message')))
        window.set_snapshot(TelemetrySnapshot(messages=messages))
        assert not window._auto_follow_messages
        assert window.message_log.count() == 3
    finally:
        window.close()


def test_view_enables_profile_reload_only_when_stopped(application):
    presenter = FakePresenter()
    window = MainWindow(presenter)
    try:
        window.set_snapshot(TelemetrySnapshot(mission_stopped=False))
        assert not window.reload_profile.isEnabled()
        window.set_snapshot(TelemetrySnapshot(mission_stopped=True))
        assert window.reload_profile.isEnabled()
    finally:
        window.close()
