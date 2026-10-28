# Bullet View flight instruments

## Goal

Add filtered vertical speed, a 0–100 m altitude scale, and degree markings to
the native attitude ball.

## Implementation

1. Add a presenter-owned filtered altitude-difference estimator.
2. Expose vertical speed in the immutable telemetry snapshot.
3. Add a vertical-speed gauge and expand the attitude ball markings.
4. Update tests and README documentation.

## Interface changes

- `TelemetrySnapshot.vertical_speed_m_s` is optional and expressed in m/s.
- No MAVLink packet or CLI changes.

## Verification

Passed: `uv run --locked --package bullet-view pytest -q` (6 passed).

## Status

Implemented

## Implementation commit

`8c3b8f1`
