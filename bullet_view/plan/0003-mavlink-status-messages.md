# MAVLink mission status messages

## Goal

Publish indexed, severity-aware mission status text from `bullet_app` and show
it in `bullet_view` with colored, scrollable history.

## Implementation

- Add a shared status catalog and UTF-8-safe MAVLink text chunking to
  `bullet_msgs`.
- Publish status changes from the app's MAVLink adapter using the existing
  human-readable status formatter.
- Decode `STATUSTEXT` in `bullet_view`, retain full history, and render the
  latest five lines with severity colors.
- Keep the catalog internal for descriptions, stop auto-follow after mission
  completion, and show a persistent description panel for the selected row.

## Verification

Run the `bullet-msgs`, `bullet-app`, and `bullet-view` pytest suites.

## Status

Pending

## Implementation commit

Pending
