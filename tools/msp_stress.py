#!/usr/bin/env python3
"""Saturate MSP attitude + altitude polling for 600 seconds (read-only)."""
import argparse
import csv
import math
from pathlib import Path
import sys
import time

# Allow running from a checkout without installing the workspace packages.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'msp_link' / 'src'))
from msp_link import Parser, SerialTransport, encode
from msp_link.commands import ATTITUDE, ALTITUDE

COMMANDS = (ATTITUDE, ALTITUDE)
NAMES = {ATTITUDE: 'attitude', ALTITUDE: 'altitude'}


def stress(transport, duration, report, *, timeout=.3):
    """One outstanding request per command, replenished immediately on reply.

    Report only validated replies, using actual monotonic interval durations.
    Abort on timeout: MSP has no sequence numbers to match retries reliably.
    """
    parser = Parser()
    packets = {command: encode(command) for command in COMMANDS}
    pending = {}
    counts = dict.fromkeys(COMMANDS, 0)
    totals = counts.copy()
    minimum = dict.fromkeys(COMMANDS, math.inf)
    maximum = dict.fromkeys(COMMANDS, 0.)
    below = dict.fromkeys(COMMANDS, 0)
    start = interval_start = time.monotonic()
    deadline = start + duration
    next_report = start + 1
    full_intervals = 0

    def emit(now, full):
        nonlocal interval_start, full_intervals
        elapsed = now - interval_start
        rates = {command: counts[command] / elapsed for command in COMMANDS}
        report(now - start, elapsed, counts.copy(), rates)
        if full:
            full_intervals += 1
            for command in COMMANDS:
                minimum[command] = min(minimum[command], rates[command])
                maximum[command] = max(maximum[command], rates[command])
                below[command] += rates[command] < 50
        counts.update(dict.fromkeys(COMMANDS, 0))
        interval_start = now

    for command in COMMANDS:
        transport.send(packets[command])
        pending[command] = time.monotonic()
    try:
        while time.monotonic() < deadline:
            messages = parser.feed(transport.receive())
            now = time.monotonic()
            if now >= next_report:
                emit(now, True)
                next_report = now + 1
            for message in messages:
                command = message.command
                if command not in pending or message.direction not in ('>', '!'):
                    continue
                if message.direction == '!':
                    raise RuntimeError(f'{NAMES[command]} rejected by firmware')
                if (command == ATTITUDE and len(message.payload) != 6) or len(message.payload) < 6:
                    raise RuntimeError(f'Invalid {NAMES[command]} payload length: {len(message.payload)}')
                del pending[command]
                counts[command] += 1
                totals[command] += 1
            for command, sent in pending.items():
                if now - sent >= timeout:
                    raise TimeoutError(f'No {NAMES[command]} reply within {timeout}s')
            if now < deadline:
                for command in COMMANDS:
                    if command not in pending:
                        transport.send(packets[command])
                        pending[command] = time.monotonic()
    finally:
        end = time.monotonic()
        if end > interval_start:
            emit(end, False)
        elapsed = end - start
        print(f'\nMeasured {elapsed:.3f}s, {full_intervals} full intervals', flush=True)
        for command in COMMANDS:
            low = minimum[command] if full_intervals else float('nan')
            print(f'{NAMES[command]}: {totals[command]} replies, '
                  f'mean={totals[command] / elapsed:.2f} Hz, '
                  f'full-interval min/max={low:.2f}/{maximum[command]:.2f} Hz, '
                  f'intervals below 50 Hz={below[command]}', flush=True)
    return full_intervals > 0 and not any(below.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', default='/dev/ttyACM1')
    parser.add_argument('--baudrate', type=int, default=115200,
                        help='Host serial baud rate, ignored by native USB VCP (default: 115200)')
    parser.add_argument('--duration', type=float, default=600, help='Seconds (default: 600)')
    parser.add_argument('--output', type=Path, help='Create a new CSV of measured intervals')
    args = parser.parse_args()
    if not math.isfinite(args.duration) or args.duration <= 0 or args.baudrate <= 0:
        parser.error('duration must be finite and positive, baudrate must be positive')
    transport = SerialTransport(args.device, args.baudrate)
    output = None
    try:
        if args.output:
            output = args.output.open('x', newline='')
        writer = csv.writer(output) if output else None
        if writer:
            writer.writerow(('elapsed_s', 'interval_s', 'attitude_replies', 'altitude_replies',
                             'attitude_hz', 'altitude_hz'))

        def report(elapsed, interval, counts, rates):
            print(f'{elapsed:7.2f}s  attitude={rates[ATTITUDE]:8.2f} Hz  '
                  f'altitude={rates[ALTITUDE]:8.2f} Hz', flush=True)
            if writer:
                writer.writerow((elapsed, interval, counts[ATTITUDE], counts[ALTITUDE],
                                 rates[ATTITUDE], rates[ALTITUDE]))
                output.flush()

        transport.open()
        transport.serial.exclusive = True
        transport.serial.reset_input_buffer()
        print(f'{args.device}, host baud={args.baudrate}, duration={args.duration}s\n'
              'Continuous MSP v1 polling, one request outstanding per message type.\n'
              'Measures reply throughput, not sensor freshness. No controller settings written.',
              flush=True)
        passed = stress(transport, args.duration, report)
        print('PASS: both >=50 Hz in every full interval.' if passed else
              'FAIL: below 50 Hz, or no full interval measured.', flush=True)
        return 0 if passed else 1
    except (OSError, ValueError, RuntimeError) as error:
        print(f'INCOMPLETE: {error}', file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print('INCOMPLETE: interrupted', file=sys.stderr)
        return 130
    finally:
        transport.close()
        if output:
            output.close()


if __name__ == '__main__':
    sys.exit(main())
