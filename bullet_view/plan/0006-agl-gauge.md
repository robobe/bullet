# Bullet View AGL gauge

## Goal

Receive standard MAVLink DISTANCE_SENSOR AGL readings and display them in the Telemetry tab with the existing MVP architecture.

## Implementation steps

1. Add immutable rangefinder model and worker conversion.
2. Propagate AGL through the presenter snapshot.
3. Add a themed dedicated AGL gauge and focused offscreen tests.

## Interface changes

- Add `Rangefinder` to `TelemetrySnapshot`.
- Parse valid and invalid DISTANCE_SENSOR packets without network logic in the view.

## Verification

- Test MAVLink conversion, presenter updates, valid/invalid display state, and existing telemetry regressions.

## Status

Implemented; focused tests passed

## Implementation commit

`0493860`
