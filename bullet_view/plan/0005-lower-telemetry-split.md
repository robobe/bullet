# Lower telemetry split

## Goal

Split the lower Telemetry area into a compact horizontal R/P/Y attitude summary
and a wider status-message panel.

## Implementation steps

1. Move the existing numeric attitude labels into a lower-left horizontal card.
2. Keep the status history and message details in the lower-right card.
3. Preserve snapshot update behavior and add Qt layout assertions.

## Interface changes

No telemetry model, MAVLink, image, or presenter interface changes.

## Verification

Run the Bullet View Qt test suite with the offscreen platform.

## Status

Pending

## Implementation commit

Pending
