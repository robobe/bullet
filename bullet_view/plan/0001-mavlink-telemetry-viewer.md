# MAVLink Telemetry Viewer

## Goal

Create `bullet_view`, a UV-managed PySide6 MVP viewer for the Bullet app's
MAVLink telemetry.

## Implementation

1. Define immutable telemetry models and a receive-only MAVLink worker.
2. Add an MVP presenter that maps worker updates to the GUI model.
3. Add FlightLens-themed telemetry and disabled Parameters tabs with a flight
   ball, altitude widget, yaw readout, and connection status.
4. Defer reconnect and parameter updates to v2.

## Verification

Passed: `uv run --locked --package bullet-view pytest -q` (5 passed).

## Status

Implemented

## Implementation commit

`8a28e85`
