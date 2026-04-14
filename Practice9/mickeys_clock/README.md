# 🕐 Mickey's Clock

A pixel-art clock application built with **Pygame**, featuring Mickey Mouse's iconic white gloves as clock hands.

```
  ╔══════════════════════════╗
  ║     Mickey's Clock       ║
  ║   ⬤  (pixel art face)   ║
  ║    ╱ min  sec ╲          ║
  ║   ●────────────●         ║
  ║      Mickey ♥            ║
  ╚══════════════════════════╝
```

## 🎯 Features

| Feature | Detail |
|---------|--------|
| **Style** | 1 : 1 pixel art (3× nearest-neighbor scaled) |
| **Right hand** | 🔴 Red glove → **Minutes** |
| **Left hand** | 🔵 Cyan glove → **Seconds** |
| **Update rate** | Every 100 ms (smooth sub-second motion) |
| **Display** | Digital `MM:SS` readout beneath the face |

## 🗂 Structure

```
mickeys_clock/
├── main.py            # Entry point & game loop
├── clock.py           # MickeyClock render class
├── generate_assets.py # One-time asset generator
├── images/
│   ├── mickey_hand_right.png   # Minute hand sprite
│   └── mickey_hand_left.png    # Second hand sprite
└── README.md
```

## 🚀 Running

```bash
# Install dependency
pip install pygame

# (Optional) Regenerate pixel-art hand sprites
python generate_assets.py

# Launch the clock
python main.py
```

## ⌨️ Controls

| Key | Action |
|-----|--------|
| `ESC` / `Q` | Quit |
| `F` | Toggle fullscreen |

## 🛠 Implementation Notes

### Pixel-Art Scaling

All rendering happens on a small logical canvas (`160 × 160` pixels), then upscaled **3×** using `pygame.transform.scale()` with nearest-neighbor interpolation.  This guarantees clean, sharp pixels at any window size.

### Hand Rotation

```python
# Convert time → degrees (0° = 12 o'clock, clockwise)
min_angle = minutes * 6 + seconds * 0.1   # smooth minute hand
sec_angle = seconds * 6

# Rotate sprite using pygame.transform.rotate()
rotated = pygame.transform.rotate(hand_src, -angle_deg)
```

`pygame.transform.rotate()` rotates **counter-clockwise**, so angles are negated to produce the familiar clockwise motion.

### Coordinate Math

```python
import math
rad = math.radians(angle_deg - 90)   # -90° shifts 0° to 12 o'clock
end_x = cx + int(length * math.cos(rad))
end_y = cy + int(length * math.sin(rad))
```

### Clock Face Elements

- **Outer bezel**: gold + dark rings for depth
- **Hour ticks**: thicker every 3rd mark (quarters)
- **Minute ticks**: single pixel dots
- **Mickey silhouette**: rendered below the clock face using circles/rects
- **Digital readout**: monospace pixel font in `MM:SS` format

## 📚 References

- [Nerd Paradise Pygame Tutorial](https://nerdparadise.com/programming/pygame)
- [StackOverflow – Rotating Graphics in Pygame](https://stackoverflow.com/questions/4183208)
- [pygame.transform.rotate docs](https://www.pygame.org/docs/ref/transform.html#pygame.transform.rotate)
