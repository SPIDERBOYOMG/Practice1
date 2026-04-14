# 🕹️ Moving Ball Game – Pixel Edition

An interactive pixel-art style game built with **pygame**.  
Move a red ball around a 600 × 600 grid using the arrow keys.

---

## 📁 Project Structure

```
Practice7/
└── moving_ball/
    ├── main.py   – game loop, rendering, HUD
    ├── ball.py   – Ball class (movement + pixel-art drawing)
    └── README.md – this file
```

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| ↑ Arrow | Move up 20 px |
| ↓ Arrow | Move down 20 px |
| ← Arrow | Move left 20 px |
| → Arrow | Move right 20 px |
| ESC / ✕ | Quit |

> **Boundary rule:** any input that would move the ball (radius 25 px) off-screen is silently ignored.

---

## ⚙️ Requirements

```
Python >= 3.8
pygame >= 2.0
```

Install pygame:

```bash
pip install pygame
```

---

## ▶️ Running the Game

```bash
cd Practice7/moving_ball
python main.py
```

---

## 🎨 Pixel-Art Design Choices

| Element | Detail |
|---------|--------|
| Background | Off-white parchment with a 20 px faint grid |
| Border | 6 px thick near-black frame with red corner accents |
| Ball | Red circle (r = 25) with a dark shadow + bright highlight dot |
| HUD | Crisp monospace (Courier New) coordinates – no antialiasing |
| Frame rate | 60 FPS via `pygame.time.Clock` |

---

## 🧩 Architecture

### `ball.py` – `Ball` class

| Method | Responsibility |
|--------|---------------|
| `__init__(w, h)` | Places ball at screen center; stores boundaries |
| `move(dx, dy)` | Validates + applies movement |
| `handle_keydown(key)` | Maps arrow keys → `move()` calls |
| `draw(surface)` | Renders shadow → body → highlight |

### `main.py`

| Function | Responsibility |
|----------|---------------|
| `draw_pixel_grid()` | Background grid lines |
| `draw_border()` | Outer frame + corner accents |
| `draw_hud()` | Live X/Y coordinates |
| `draw_instructions()` | Bottom hint bar |
| `main()` | pygame init, event loop, frame timing |
