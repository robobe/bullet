# Telemetry log controls and timestamps

Add Clear log and a checked-by-default, user-controlled Auto-scroll checkbox
to the status-message header. Completion must not change the checkbox.

Capture the latest viewer image's simulation time and sequence in each status
message at arrival. Render `[12.345 / 123] message`, replacing the catalog prefix;
retain raw text, index, and severity for details. Missing values display `—`.
Image simulation time comes from descriptor source metadata, not wall time.

Clear presenter history and reset the list, selection, details, and append counter
without resetting simulation time or Auto-scroll. Update the README.

Validate metadata with and without simulation time, immutable per-message context,
formatting, clearing followed by arrivals, severity/details, and manual scrolling
including completion, using focused tests and the offscreen bullet_view suite.

## Status

Pending implementation commit. No protocol or publisher changes. Latest-frame
context may lag status events and is unavailable in telemetry-only mode.
