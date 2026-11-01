from bullet_view.model import Bbox, ImageFrame, StatusText, TelemetryUpdate
from bullet_view.presenter import Presenter, VerticalSpeedEstimator
from bullet_view.worker import MavlinkWorker
import pytest


class Message:
    def __init__(self, kind, **fields):
        self.kind = kind
        self.__dict__.update(fields)

    def get_type(self):
        return self.kind


def test_worker_maps_standard_mavlink_messages_to_updates():
    worker = MavlinkWorker('test')
    updates = []
    worker.update.connect(updates.append)
    worker._emit_message(Message('ATTITUDE', roll=.1, pitch=.2, yaw=.3, time_boot_ms=4), 1.)
    worker._emit_message(Message('ALTITUDE', altitude_local=5., time_usec=6), 2.)
    worker._emit_message(Message('HEARTBEAT'), 3.)
    worker._emit_message(Message('DISTANCE_SENSOR', current_distance=275, time_boot_ms=7), 4.)

    assert [update.kind for update in updates] == ['ATTITUDE', 'ALTITUDE', 'HEARTBEAT', 'DISTANCE_SENSOR']
    assert updates[0].value.roll_rad == .1
    assert updates[1].value.local_m == 5.
    assert updates[3].value.distance_cm == 275.


def test_worker_marks_distance_sensor_sentinel_invalid():
    worker = MavlinkWorker('test')
    updates = []
    worker.update.connect(updates.append)
    worker._emit_message(Message('DISTANCE_SENSOR', current_distance=65535, time_boot_ms=7), 1.)
    assert not updates[0].value.valid
    assert updates[0].value.distance_cm is None


def test_worker_maps_status_text_and_index():
    worker = MavlinkWorker('test')
    updates = []
    worker.update.connect(updates.append)
    worker._emit_message(Message('STATUSTEXT', severity=4, text='[07] warning'), 1.)
    assert updates[0].kind == 'STATUSTEXT'
    assert updates[0].value.index == 7
    assert updates[0].value.severity == 4
    assert updates[0].value.text == '[07] warning'


def test_worker_reassembles_bbox_named_values():
    worker = MavlinkWorker('test')
    updates = []
    worker.update.connect(updates.append)
    for name, value in (('BBOX_VALID', 1.), ('BBOX_X', 10.), ('BBOX_Y', 20.),
                        ('BBOX_W', 30.), ('BBOX_H', 40.)):
        worker._emit_message(Message('NAMED_VALUE_FLOAT', name=name.encode(), value=value), 1.)

    assert updates[-1].kind == 'BBOX'
    assert updates[-1].value == Bbox(True, 10., 20., 30., 40.)


def test_worker_does_not_retry_after_connection_failure():
    calls = []

    def fail(endpoint):
        calls.append(endpoint)
        raise OSError('offline')

    worker = MavlinkWorker('test', connection_factory=fail)
    errors = []
    worker.failed.connect(errors.append)
    worker.run()

    assert calls == ['test']
    assert errors == ['offline']


def test_presenter_only_reports_connected_after_a_message():
    presenter = Presenter('test')
    statuses = []
    presenter.status_changed.connect(statuses.append)

    presenter._set_status('Listening for MAVLink telemetry')
    assert not presenter.snapshot.connected
    presenter._on_update(TelemetryUpdate('HEARTBEAT', None, 1.))

    assert presenter.snapshot.connected
    assert statuses[-1] == 'Connected'


def test_presenter_retains_status_messages_in_snapshot():
    presenter = Presenter('test')
    presenter._on_update(TelemetryUpdate('STATUSTEXT', StatusText(2, 4, '[02] warning', 1.), 1.))
    assert presenter.snapshot.messages[0].severity == 4


def test_presenter_captures_frame_context_and_clears_history():
    presenter = Presenter('test')
    update = TelemetryUpdate('STATUSTEXT', StatusText(1, 6, '[01] ready', 1.), 1.)
    presenter._on_update(update)
    assert presenter.snapshot.messages[0].frame_id is None
    assert presenter.snapshot.messages[0].simulation_time_s is None
    presenter._on_frame(ImageFrame(2, 2, 'rgb8', bytes(12), 1, 100, 0.))
    presenter._on_update(update)
    presenter._on_frame(ImageFrame(2, 2, 'rgb8', bytes(12), 2, 200, 1.5))
    assert presenter.snapshot.messages[-1].simulation_time_s == 0.
    assert presenter.snapshot.messages[-1].frame_id == 1
    snapshots = []
    presenter.snapshot_changed.connect(snapshots.append)
    presenter.clear_messages()
    assert snapshots[-1].messages == ()
    assert presenter.snapshot.image.sequence == 2
    presenter.clear_messages()
    presenter._on_update(update)
    assert len(presenter.snapshot.messages) == 1
    assert presenter.snapshot.messages[0].frame_id == 2
    assert presenter.snapshot.messages[0].simulation_time_s == 1.5


def test_vertical_speed_estimator_filters_altitude_rate_and_resets_after_gap():
    estimator = VerticalSpeedEstimator()

    assert estimator.update(10., 1.) is None
    assert estimator.update(11., 1.1) == pytest.approx(10.)
    assert estimator.update(11.5, 1.2) == pytest.approx(8.75)
    assert estimator.update(20., 3.) is None
