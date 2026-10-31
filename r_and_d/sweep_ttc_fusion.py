"""Compare alpha-beta TTC coefficients against the retrospective hit-time oracle."""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from run_ttc_fusion import load_samples
from ttc_fusion import AlphaBetaTtcFilter


COEFFICIENTS = ((.15, .02), (.25, .05), (.35, .08), (.50, .10))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sqlite_path', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    hit_time, measurements = load_samples(args.sqlite_path)
    times = np.array([measurement.time_s for measurement in measurements])
    truth = hit_time - times
    output = args.output or args.sqlite_path.with_name('ttc-fusion-coefficient-sweep.png')
    limit = max(18., float(np.max(truth)) * 1.05)
    figure, axis = plt.subplots(figsize=(8, 7), constrained_layout=True)
    colors = ('#4c78a8', '#d62728', '#2ca02c', '#9467bd')
    for (alpha, beta), color in zip(COEFFICIENTS, colors):
        estimator = AlphaBetaTtcFilter(alpha=alpha, beta=beta)
        values = np.array([estimator.update(measurement) for measurement in measurements])
        error = values - truth
        rmse = float(np.sqrt(np.mean(error ** 2)))
        bias = float(np.mean(error))
        axis.scatter(values, truth, s=22, alpha=.58, color=color, edgecolor='white', linewidth=.3,
                     label=f'α={alpha:.2f}, β={beta:.2f} · RMSE={rmse:.2f}s · bias={bias:+.2f}s')
    axis.plot([0, limit], [0, limit], '--', color='#333333', linewidth=1.8, label='Ideal: y=x')
    axis.set(xlim=(0, limit), ylim=(0, limit), xlabel='Filtered TTC estimate (s)',
             ylabel='Ground-truth TTC to target hit (s)', title='Alpha-beta TTC coefficient sweep')
    axis.set_aspect('equal', adjustable='box')
    axis.grid(True, alpha=.25)
    axis.legend(loc='upper left', fontsize=8)
    axis.text(.98, .03, 'Ground truth is used only for retrospective evaluation.', transform=axis.transAxes,
              ha='right', va='bottom', fontsize=9, bbox=dict(facecolor='white', alpha=.9, edgecolor='#ccc'))
    figure.savefig(output, dpi=180)
    print(output)


if __name__ == '__main__':
    main()
