from bullet_view.model import Altitude, Attitude, Rangefinder, StatusText, TelemetrySnapshot, TelemetryUpdate


def test_telemetry_models_are_immutable_and_explicit():
    snapshot = TelemetrySnapshot(attitude=Attitude(.1, .2, .3, 10), altitude=Altitude(4., 20))
    assert snapshot.attitude.yaw_rad == .3
    assert TelemetryUpdate('HEARTBEAT', None, 1.).kind == 'HEARTBEAT'
    assert TelemetrySnapshot(messages=(StatusText(1, 6, '[01] ready', 1.),)).messages[0].index == 1
    assert TelemetrySnapshot(rangefinder=Rangefinder(275., 7, True)).rangefinder.valid
