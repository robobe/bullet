# Bullet View

Bullet View is a read-only MAVLink telemetry and local camera window for Bullet
flight runs.

Mission `STATUSTEXT` messages are shown in the Telemetry tab with their MAVLink
severity color. The log keeps the full session history, follows the newest five
lines during the mission, and becomes manually scrollable after completion.
Click a message to inspect its severity, index, received text, and description.
When the vehicle is stopped, use **Reload mission profile** to ask the app to
reread its mission YAML before the next scenario start.
It uses the same dark blue/teal visual theme as FlightLens. Local mode reads
the camera descriptor from ZMQ and pixels from SHM, then overlays bbox values
received through MAVLink named values. Remote mode is telemetry-only until the
v2 stream viewer is implemented.

## Run

```bash
uv run --locked --package bullet-view bullet-view
```

The default input is `udpin:0.0.0.0:14550`. Override it with:

```bash
uv run --locked --package bullet-view bullet-view --mavlink-endpoint udpin:0.0.0.0:14550
```

Local image transport can be overridden with `--image-endpoint` and
`--image-topic`. The Telemetry tab's Image mode selector switches between Local
and the telemetry-only Remote placeholder.

`bullet-app` mission runs publish to that port by default. Start both commands
with the same port, or override the app's `--mavlink-endpoint` output and this
viewer's input together.

V1 displays HEARTBEAT, ATTITUDE, ALTITUDE, filtered vertical speed, local camera
frames, and bbox overlays. The altitude gauge spans 0–100 m. Parameter updates,
automatic reconnects, and remote image streaming are intentionally deferred to
v2.
