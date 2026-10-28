from bullet_view.model import Altitude, Attitude, TelemetrySnapshot, TelemetryUpdate


def test_telemetry_models_are_immutable_and_explicit():
    snapshot = TelemetrySnapshot(attitude=Attitude(.1, .2, .3, 10), altitude=Altitude(4., 20))
    assert snapshot.attitude.yaw_rad == .3
    assert TelemetryUpdate('HEARTBEAT', None, 1.).kind == 'HEARTBEAT'
