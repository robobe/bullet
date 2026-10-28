"""Immutable telemetry state shared by the presenter and view."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Attitude:
    roll_rad: float
    pitch_rad: float
    yaw_rad: float
    time_boot_ms: int


@dataclass(frozen=True)
class Altitude:
    local_m: float
    time_usec: int


@dataclass(frozen=True)
class TelemetrySnapshot:
    connected: bool = False
    heartbeat_at_s: float | None = None
    last_message_at_s: float | None = None
    attitude: Attitude | None = None
    altitude: Altitude | None = None
    error: str | None = None
    vertical_speed_m_s: float | None = None


@dataclass(frozen=True)
class TelemetryUpdate:
    kind: str
    value: object
    received_at_s: float
