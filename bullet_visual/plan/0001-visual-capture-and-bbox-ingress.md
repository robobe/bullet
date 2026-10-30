# Visual capture and bbox ingress

## Goal

Move image capture and perception into `bullet_visual`, support ZMQ/SHM, USB, and MIPI sources, and make `bullet_app` consume visual detections over a dedicated ZMQ endpoint.

## Implementation steps

- Add the uv project, copied project guidance, strict YAML source configuration, and source adapters.
- Run latest-frame capture/detection/publishing workers using `bullet_perception`.
- Preserve v2 identity for ZMQ/SHM and emit valid v1 identity for direct cameras.
- Replace bullet_app inline vision with visual ingress and v1 enrichment while preserving recorder output.
- Add workspace/task integration and unit/in-process integration coverage.

## Interface changes

- New `bullet_visual` YAML and `--config` CLI.
- New visual ingress endpoint `tcp://127.0.0.1:5560`.
- Existing recorder-facing bbox endpoint `tcp://127.0.0.1:5558` remains unchanged.

## Verification

- Run focused bullet_visual and bullet_app tests.
- Run the locked workspace test suite and `git diff --check`.

## Scope and defaults

- One selected source per process; no fallback or reconnect in v1.
- OpenCV plus GStreamer is used for USB/MIPI.
- Direct-camera v1 detections are enriched in bullet_app only when a current identity exists and the frame is fresh.

## Status

Complete.

## Implementation commit

`91d45b9`
