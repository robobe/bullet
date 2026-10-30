# Bullet Visual

`bullet_visual` captures one configured image source, runs the shared
`bullet_perception` detector, and publishes `tracking/front/bbox` messages to
`bullet_app` on `tcp://127.0.0.1:5560`.

The source is selected in YAML (`zmq_shm`, `usb`, or `mipi`). The process uses a
latest-frame buffer so detector latency cannot create an unbounded control delay.

```bash
uv run --locked --package bullet-visual bullet-visual --config config/zmq.yaml
```

`zmq_shm` preserves Bullet v2 source identity. USB and MIPI emit schema-valid v1
identity using a generated session, sequence, and monotonic capture timestamp.
