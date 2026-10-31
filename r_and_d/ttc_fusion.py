"""Causal alpha-beta TTC filter for offline replay and future live adapters."""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class TtcMeasurement:
    time_s: float
    ttc_s: float
    relative_residual: float | None = None


class AlphaBetaTtcFilter:
    """Track TTC and its rate using only current and previous measurements."""

    def __init__(self, *, alpha=0.25, beta=0.05, max_residual=0.15):
        if not 0 < alpha <= 1 or not 0 < beta <= 1:
            raise ValueError('alpha and beta must be in (0, 1]')
        if not isfinite(max_residual) or max_residual <= 0:
            raise ValueError('max_residual must be positive')
        self.alpha = alpha
        self.beta = beta
        self.max_residual = max_residual
        self.reset()

    def reset(self):
        self.ttc_s = None
        self.rate_s_s = 0.0
        self.time_s = None

    def update(self, measurement: TtcMeasurement):
        if (not isfinite(measurement.time_s) or not isfinite(measurement.ttc_s)
                or measurement.ttc_s <= 0):
            self.reset()
            return None
        if self.ttc_s is None:
            self.ttc_s = measurement.ttc_s
            self.time_s = measurement.time_s
            return self.ttc_s
        dt = measurement.time_s - self.time_s
        if not isfinite(dt) or dt <= 0:
            self.reset()
            return self.update(measurement)
        predicted = self.ttc_s + self.rate_s_s * dt
        innovation = measurement.ttc_s - predicted
        quality = 1.0
        if measurement.relative_residual is not None and isfinite(measurement.relative_residual):
            quality = max(0.1, min(1.0, 1.0 - measurement.relative_residual / self.max_residual))
        alpha = self.alpha * quality
        beta = self.beta * quality
        self.ttc_s = max(0.0, predicted + alpha * innovation)
        self.rate_s_s += beta * innovation / dt
        self.time_s = measurement.time_s
        return self.ttc_s
