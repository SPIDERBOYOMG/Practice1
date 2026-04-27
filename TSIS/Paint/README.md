# TSIS 2 — Paint Application: Extended Drawing Tools

A fully-featured paint application built with **Python + Pygame**.  
Extends the Practice 10–11 base with six new capabilities required for TSIS 2.

---

## How to Run

```bash
pip install pygame
python paint.py
```

---

## Features

### From Practice 10–11 (base)
| Tool | Key | Description |
|------|-----|-------------|
| Rectangle | `R` | Click-drag outline or filled rectangle |
| Circle | `O` | Click-drag outline or filled circle |
| Eraser | `E` | Paints over with canvas background |
| Square | `Q` | Constrained equal-side rectangle |
| Right Triangle | `A` | Right-angle at start point |
| Equilateral Triangle | `B` | Symmetric triangle from baseline |
| Rhombus | `M` | Diamond shape from bounding box |

### New in TSIS 2
| Tool | Key | Description |
|------|-----|-------------|
| **Pencil** | `P` | Freehand drawing — continuous `draw.line` between mouse positions |
| **Straight Line** | `L` | Click to set start, drag to end — live ghost preview while dragging |
| **Flood Fill** | `G` | BFS fill via `PixelArray`; stops at exact-color boundaries |
| **Text** | `T` | Click canvas → type → `Enter` commits, `Escape` cancels |

### Brush Sizes
Three preset sizes apply to **all** tools (pencil, line, all shapes):

| Key | Button | Size |
|-----|--------|------|
| `1` | S | 2 px |
| `2` | M | 5 px |
| `3` | L | 10 px |

`[` / `]` fine-tune the active size by ±1 px.

### Other Shortcuts
| Key | Action |
|-----|--------|
| `F` | Toggle filled / outline for closed shapes |
| `C` | Clear canvas |
| `Ctrl+Z` | Undo (up to 20 steps) |
| `Ctrl+S` | Save canvas as `paint_YYYYMMDD_HHMMSS.png` |
| `Escape` | Quit (or cancel active text input) |

---

## Project Structure

```
TSIS2/
├── paint.py      — main application (window, event loop, UI)
├── tools.py      — drawing helpers (flood_fill, shape geometry, draw_shape)
└── README.md
```

### Module Responsibilities

**`tools.py`**
- `flood_fill(surface, start_pos, fill_color)` — BFS using `pygame.PixelArray`
- `draw_shape(surf, tool, p1, p2, color, filled, width)` — unified shape dispatcher
- Geometry helpers: `rect_from_two_points`, `square_from_two_points`, `circle_from_two_points`, `right_triangle_points`, `equilateral_triangle_points`, `rhombus_points`

**`paint.py`**
- `Canvas` — surface + undo history (20 snapshots), save, fill, pencil, erase
- `Toolbar` — hit-tested buttons, size selectors, palette swatches
- `ShapePreview` — alpha-blended ghost overlay during drag operations
- `TextInput` — blinking cursor, live render, commit/cancel lifecycle
- `draw_cursor` — crosshair + size ring custom cursor (hides system cursor)
- `draw_status` — bottom status bar with tool / size / position readout

---

## Implementation Notes

**Pencil** uses `pygame.draw.line` between consecutive `MOUSEMOTION` positions plus a filled circle cap at each point to avoid gaps at fast movement speeds.

**Flood Fill** uses BFS over `pygame.PixelArray` (direct pixel access) rather than `get_at`/`set_at` per pixel, which is significantly faster on large canvases.

**Text Tool** renders a live preview on the screen surface (not canvas) each frame and only blits the final `font.render` onto the canvas when `Enter` is pressed — so it is non-destructive until confirmed.

**Undo** snapshots the entire canvas surface after each committed operation (`Canvas.commit()`). The snapshot list is capped at 20 entries; the oldest is dropped when the limit is exceeded.

**Save** uses `pygame.image.save(surface, filename)` with a `datetime`-based filename (`paint_YYYYMMDD_HHMMSS.png`) saved next to `paint.py`.
