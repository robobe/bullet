"""Replay native TTC through the R&D alpha-beta filter and plot the result."""
import argparse
from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import numpy as np

from ttc_fusion import AlphaBetaTtcFilter, TtcMeasurement


def load_samples(path):
    connection = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    try:
        hit_time = connection.execute(
            "select duration_s from episodes where outcome like '%target_hit%' order by id desc limit 1"
        ).fetchone()[0]
        rows = connection.execute(
            "select time_s, value from telemetry "
            "where topic='tracking/front/los' and path='optical_ttc_s' order by time_s"
        ).fetchall()
        residuals = dict(connection.execute(
            "select time_s, value from telemetry "
            "where topic='tracking/front/los' and path='ttc_relative_residual'"
        ).fetchall())
    finally:
        connection.close()
    return hit_time, [TtcMeasurement(time, value, residuals.get(time)) for time, value in rows]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sqlite_path', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    hit_time, measurements = load_samples(args.sqlite_path)
    estimator = AlphaBetaTtcFilter()
    filtered = np.array([estimator.update(measurement) for measurement in measurements])
    times = np.array([measurement.time_s for measurement in measurements])
    raw = np.array([measurement.ttc_s for measurement in measurements])
    truth = hit_time - times
    output = args.output or args.sqlite_path.with_name('ttc-fusion.png')
    error = filtered - truth
    print(f'samples={len(filtered)} rmse={np.sqrt(np.mean(error ** 2)):.3f}s '
          f'bias={np.mean(error):+.3f}s output={output}')
    figure, axis = plt.subplots(figsize=(12, 6.5), constrained_layout=True)
    axis.plot(times, raw, color='#9aa4b2', alpha=.5, marker='.', linewidth=1, label='Recorded optical TTC')
    axis.plot(times, filtered, color='#d62728', linewidth=2, label='Alpha-beta filtered TTC')
    axis.plot(times, truth, color='#4c78a8', linestyle='--', linewidth=1.8, label='Ground truth to target hit')
    axis.set(title='R&D alpha-beta TTC filter', xlabel='Flight time (s)', ylabel='TTC (s)')
    axis.set_ylim(0, max(14., float(np.max(raw)) * 1.05))
    axis.grid(True, alpha=.25)
    axis.legend(loc='upper right')
    axis.text(.01, .02, 'Ground truth is used only for retrospective evaluation. '
              'The filter uses TTC and fit residual only.', transform=axis.transAxes,
              fontsize=9, color='#444', bbox=dict(facecolor='white', alpha=.88, edgecolor='#ccc'))
    figure.savefig(output, dpi=180)


if __name__ == '__main__':
    main()
