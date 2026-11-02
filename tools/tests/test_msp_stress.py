import importlib.util
from pathlib import Path
import time

import pytest

spec = importlib.util.spec_from_file_location('msp_stress', Path(__file__).parents[1] / 'msp_stress.py')
stress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stress)


class Controller:
    def __init__(self, mode='ok'):
        self.buffer = b''
        self.sent = []
        self.mode = mode

    def send(self, packet):
        command = stress.Parser().feed(packet)[0].command
        self.sent.append(command)
        if self.mode == 'silent':
            return
        payload = b'\0' * (3 if self.mode == 'short' else 6)
        self.buffer += stress.encode(command, payload,
                                     direction='!' if self.mode == 'reject' else '>')

    def receive(self):
        time.sleep(.001)
        data, self.buffer = self.buffer[:5], self.buffer[5:]
        return data


def test_counts_fragmented_replies_and_only_sends_read_commands():
    controller = Controller()
    rows = []
    assert stress.stress(controller, 1.05, lambda *row: rows.append(row))
    assert set(controller.sent) == {108, 109}
    assert rows[0][3][108] >= 50 and rows[0][3][109] >= 50
    for _, interval, counts, rates in rows:
        assert rates[108] == counts[108] / interval
    assert sum(row[2][108] for row in rows) <= controller.sent.count(108)


@pytest.mark.parametrize('mode,error', [('silent', TimeoutError), ('reject', RuntimeError),
                                       ('short', RuntimeError)])
def test_failures_never_count_as_success(mode, error):
    rows = []
    with pytest.raises(error):
        stress.stress(Controller(mode), .1, lambda *row: rows.append(row), timeout=.01)
    assert all(sum(row[2].values()) == 0 for row in rows)
