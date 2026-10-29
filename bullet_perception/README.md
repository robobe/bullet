# Bullet Perception

Reusable image perception utilities for the Bullet workspace.

`bullet_perception.detect_bbox` accepts a nonempty H×W×3 `uint8` BGR NumPy
array and returns `(x, y, width, height)` for the largest qualifying red
target, or `None` when no target is detected. The input array is preserved.

```python
from bullet_perception import detect_bbox

bbox = detect_bbox(frame_bgr)
```

The detector uses the existing Bullet HSV thresholds and minimum contour
dimensions; this package extraction does not change detection behavior.
