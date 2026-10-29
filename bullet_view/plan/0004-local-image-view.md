# Local image view and telemetry layout

## Goal

Move camera visualization from `bullet_app` into Bullet View, supporting local
ZMQ/SHM frames and a telemetry-only remote mode placeholder.

## Implementation steps

1. Add local image and MAVLink bbox workers/models to Bullet View.
2. Publish/decode bbox named values through the existing MAVLink telemetry path.
3. Redesign the Telemetry tab and remove Bullet App camera windows.
4. Add focused worker, protocol, and Qt layout tests.

## Interface changes

Local mode reads the configured image ZMQ descriptor topic and SHM slots. Bbox
coordinates use `NAMED_VALUE_FLOAT` names `BBOX_VALID`, `BBOX_X`, `BBOX_Y`,
`BBOX_W`, and `BBOX_H`, in source-image pixels.

## Verification

Run focused Bullet View and Bullet App tests, then the locked workspace checks.

## Status

Pending

## Implementation commit

Pending
