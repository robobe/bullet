from bullet_view.model import TelemetryUpdate
from bullet_view.presenter import Presenter
from bullet_view.worker import MavlinkWorker


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

    assert [update.kind for update in updates] == ['ATTITUDE', 'ALTITUDE', 'HEARTBEAT']
    assert updates[0].value.roll_rad == .1
    assert updates[1].value.local_m == 5.


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
