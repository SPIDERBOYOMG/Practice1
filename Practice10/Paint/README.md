# 🎨 Paint Extended — Pixel Retro Edition

Extension of the **nerdparadise.com/programming/pygame/part6** paint tutorial.

---

## New Features Added

| Feature | Details |
|---|---|
| **Rectangle tool** | Click-drag to draw; toggle filled/outline with `F` |
| **Circle tool** | Click-drag from center; shows live ghost preview |
| **Eraser** | Variable-size eraser that restores the canvas texture |
| **Retro color palette** | 24-color PICO-8–inspired palette with clickable swatches |
| **Live shape preview** | Translucent ghost shape while dragging |
| **Undo** | Up to 20 steps via `Ctrl+Z` |
| **Save** | Exports canvas as `paint_save.png` with `S` |
| **Status bar** | Always-visible tool info and cursor coordinates |
| **Custom cursor** | Crosshair + brush-size circle |

---

## Run

```bash
pip install pygame
python main.py
```

---

## Controls

### Keyboard

| Key | Action |
|---|---|
| `1` | Pencil (freehand) |
| `2` | Rectangle |
| `3` | Circle |
| `4` | Eraser |
| `F` | Toggle fill / outline (rect & circle) |
| `[` / `]` | Decrease / Increase brush size |
| `C` | Clear canvas |
| `Ctrl+Z` | Undo |
| `S` | Save PNG |
| `Esc` | Quit |

### Mouse

| Input | Action |
|---|---|
| Left click + drag | Draw / shape |
| Right click | Shrink brush size (Part 6 mechanic) |
| Click palette swatch | Change color |
| Click tool button | Switch tool |
| Click FILL toggle | Toggle fill mode |

---

## Architecture

| Class | Role |
|---|---|
| `Canvas` | Pygame Surface wrapper with undo history & draw primitives |
| `Toolbar` | Left-side UI panel — tools, palette, fill toggle, radius display |
| `ShapePreview` | Translucent ghost shape rendered during rect/circle drag |
| `draw_cursor()` | Custom crosshair + brush-size circle cursor |
| `draw_status()` | Bottom status bar with tool info |

---

## Colour Palette

24 hand-picked retro colours organized in rows:

- **Row 0** — Greys / neutrals (black → white)
- **Row 1** — Reds, oranges, yellows, greens
- **Row 2** — Blues, purples, pinks
- **Row 3** — High-saturation punchy accents
