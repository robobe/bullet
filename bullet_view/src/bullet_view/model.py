"""Immutable telemetry state shared by the presenter and view."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Attitude:
    roll_rad: float
    pitch_rad: float
    yaw_rad: float
    time_boot_ms: int


@dataclass(frozen=True)
class Heartbeat:
    base_mode: int
    system_status: int
    received_at_s: float


@dataclass(frozen=True)
class Altitude:
    local_m: float
    time_usec: int


@dataclass(frozen=True)
class StatusText:
    index: int
    severity: int
    text: str
    received_at_s: float


@dataclass(frozen=True)
class Bbox:
    valid: bool
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None


@dataclass(frozen=True)
class ImageFrame:
    width: int
    height: int
    encoding: str
    pixels: bytes
    sequence: int
    capture_ns: int


@dataclass(frozen=True)
class TelemetrySnapshot:
    connected: bool = False
    heartbeat_at_s: float | None = None
    last_message_at_s: float | None = None
    attitude: Attitude | None = None
    altitude: Altitude | None = None
    error: str | None = None
    vertical_speed_m_s: float | None = None
    messages: tuple[StatusText, ...] = ()
    heartbeat: Heartbeat | None = None
    mission_stopped: bool = False
    bbox: Bbox | None = None
    image: ImageFrame | None = None


@dataclass(frozen=True)
class TelemetryUpdate:
    kind: str
    value: object
    received_at_s: float
