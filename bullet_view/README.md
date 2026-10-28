# Bullet View

Bullet View is a read-only MAVLink telemetry window for Bullet flight runs.
It uses the same dark blue/teal visual theme as FlightLens.

## Run

```bash
uv run --locked --package bullet-view bullet-view
```

The default input is `udpin:0.0.0.0:14550`. Override it with:

```bash
uv run --locked --package bullet-view bullet-view --mavlink-endpoint udpin:0.0.0.0:14550
```

`bullet-app` mission runs publish to that port by default. Start both commands
with the same port, or override the app's `--mavlink-endpoint` output and this
viewer's input together.

V1 displays HEARTBEAT, ATTITUDE, and ALTITUDE telemetry. Parameter updates and
automatic reconnects are intentionally deferred to v2.
