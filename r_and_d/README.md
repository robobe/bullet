# TTC fusion R&D

This prototype filters qualified optical TTC samples without using ground truth
at runtime. It uses a causal alpha-beta state estimator with state
`(TTC, TTC rate)` and optionally lowers its gains when the recorded TTC fit
residual is high.

Run it against the FlightLens SQLite sidecar:

```bash
python3 r_and_d/run_ttc_fusion.py recordings/bullet_landscape_*.mcap.flightlens.sqlite
```

The script writes `ttc-fusion.png` beside the SQLite input. Ground truth is
used only for retrospective metrics and the graph overlay.

Generate the coefficient comparison:

```bash
python3 r_and_d/sweep_ttc_fusion.py recordings/bullet_landscape_*.mcap.flightlens.sqlite
```
