"""
Paint Extended — TSIS 2
=======================
Builds on Practice 10–11 (rectangle, circle, eraser, color picker,
square, right triangle, equilateral triangle, rhombus).

New in TSIS 2
-------------
  Pencil    — freehand drawing along cursor path
  Line      — click-drag straight line with live preview
  Brush sizes — 1/2/3 keys  →  small (2 px), medium (5 px), large (10 px)
  Fill      — flood-fill a closed region (BFS via PixelArray)
  Text      — click to place, type, Enter confirms, Escape cancels
  Ctrl+S    — save canvas as timestamped .png

Keyboard shortcuts
------------------
  P         Pencil         L  Line
  R         Rectangle      O  Circle
  Q         Square
  A         Right triangle B  Equilateral triangle
  M         Rhombus        E  Eraser
  G         Fill (bucket)  T  Text
  1 / 2 / 3 Brush size (small / medium / large)
  F         Toggle fill / outline for closed shapes
  [ / ]     Fine-tune brush size (−1 / +1 px)
  C         Clear canvas
  Ctrl+Z    Undo (up to 20 steps)
  Ctrl+S    Save as timestamped PNG
  Escape    Quit  (also cancels text input mid-entry)
"""

import sys
import os
import math
import datetime
import pygame
from tools import (
    flood_fill, draw_shape,
    rect_from_two_points, square_from_two_points,
    circle_from_two_points, right_triangle_points,
    equilateral_triangle_points, rhombus_points,
)


# ───────────────────────────────────────────────────────────────────────────────
# Constants
# ───────────────────────────────────────────────────────────────────────────────

CANVAS_W, CANVAS_H = 800, 540
TOOLBAR_W          = 130
WINDOW_W           = CANVAS_W + TOOLBAR_W
WINDOW_H           = CANVAS_H + 22     # 22px status bar
FPS                = 60

BRUSH_SIZES = [2, 5, 10]   # small, medium, large

# Retro PICO-8-inspired palette ────────────────────────────────────────────────
PALETTE = [
    (0,   0,   0),    (29,  29,  29),  (73,  73,  73),
    (122, 122, 122),  (179, 179, 179), (255, 255, 255),
    (190, 38,  51),   (224, 111, 139), (228, 166, 114),
    (254, 231, 97),   (99,  199, 77),  (62,  137, 72),
    (36,  82,  59),   (0,   87,  132), (0,   149, 233),
    (154, 232, 254),  (120, 70,  184), (215, 123, 186),
    (255, 0,   77),   (255, 163, 0),   (0,   255, 102),
    (41,  173, 255),  (131, 118, 156), (194, 195, 199),
]

# Colours ──────────────────────────────────────────────────────────────────────
C_TOOLBAR_BG   = (22,  18,  30)
C_TOOLBAR_EDGE = (60,  50,  80)
C_TOOL_NORMAL  = (38,  32,  52)
C_TOOL_HOVER   = (58,  50,  78)
C_TOOL_ACTIVE  = (108, 82,  180)
C_TOOL_BORDER  = (80,  65,  110)
C_TEXT         = (245, 238, 255)
C_TEXT_DIM     = (175, 165, 200)
C_CANVAS_BG    = (245, 242, 235)
C_TEXT_CURSOR  = (30, 144, 255)

# Tools ────────────────────────────────────────────────────────────────────────
# Arranged in 2-column grid inside the toolbar
TOOL_GRID = [
    ("PENCIL",  "P"),  ("LINE",   "L"),
    ("RECT",    "R"),  ("CIRCLE", "O"),
    ("SQUARE",  "Q"),  ("RTRI",   "A"),
    ("EQTRI",   "B"),  ("RHOMBUS","M"),
    ("ERASER",  "E"),  ("FILL",   "G"),
    ("TEXT",    "T"),  (None,     None),   # padding
]

KEY_TO_TOOL = {
    pygame.K_p: "PENCIL",  pygame.K_l: "LINE",
    pygame.K_r: "RECT",    pygame.K_o: "CIRCLE",
    pygame.K_q: "SQUARE",  pygame.K_a: "RTRI",
    pygame.K_b: "EQTRI",   pygame.K_m: "RHOMBUS",
    pygame.K_e: "ERASER",  pygame.K_g: "FILL",
    pygame.K_t: "TEXT",
}

SHAPE_TOOLS = {"RECT", "CIRCLE", "SQUARE", "RTRI", "EQTRI", "RHOMBUS", "LINE"}
POLY_TOOLS  = {"RTRI", "EQTRI", "RHOMBUS"}


# ───────────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────────

def load_font(size: int, bold: bool = False) -> pygame.font.Font:
    for name in ("Courier New", "Courier", "monospace", None):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)


def rr(surf, color, rect, radius=6, width=0):
    pygame.draw.rect(surf, color, rect, width, border_radius=radius)


def checkerboard(w: int, h: int, tile: int = 12) -> pygame.Surface:
    surf = pygame.Surface((w, h))
    c1, c2 = (245, 242, 235), (228, 223, 212)
    for row in range(h // tile + 1):
        for col in range(w // tile + 1):
            c = c1 if (row + col) % 2 == 0 else c2
            pygame.draw.rect(surf, c, (col * tile, row * tile, tile, tile))
    return surf


def timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


# ───────────────────────────────────────────────────────────────────────────────
# Tool icon renderer
# ───────────────────────────────────────────────────────────────────────────────

def draw_tool_icon(surf, name: str, cx: int, cy: int, color, size: int = 14):
    s = size // 2
    if name == "PENCIL":
        pts = [(cx-s, cy+s), (cx-s+3, cy+s), (cx+s, cy-s+3),
               (cx+s, cy-s), (cx+s-3, cy-s), (cx-s, cy+s-3)]
        pygame.draw.polygon(surf, color, pts)
        tip = [(cx-s, cy+s), (cx-s+3, cy+s), (cx-s, cy+s-3)]
        pygame.draw.polygon(surf, (255, 220, 80), tip)
    elif name == "LINE":
        pygame.draw.line(surf, color, (cx-s, cy+s), (cx+s, cy-s), 3)
        pygame.draw.circle(surf, color, (cx-s, cy+s), 2)
        pygame.draw.circle(surf, color, (cx+s, cy-s), 2)
    elif name == "RECT":
        r = pygame.Rect(cx-s, cy-s+2, size, size-4)
        pygame.draw.rect(surf, color, r, 2, border_radius=1)
    elif name == "CIRCLE":
        pygame.draw.circle(surf, color, (cx, cy), s, 2)
    elif name == "SQUARE":
        r = pygame.Rect(cx-s+1, cy-s+1, size-2, size-2)
        pygame.draw.rect(surf, color, r, 2)
    elif name == "RTRI":
        pts = [(cx-s, cy+s), (cx+s, cy+s), (cx-s, cy-s)]
        pygame.draw.polygon(surf, color, pts, 2)
    elif name == "EQTRI":
        h = int(size * math.sqrt(3) / 2)
        pts = [(cx-s, cy+h//2), (cx+s, cy+h//2), (cx, cy-h//2)]
        pygame.draw.polygon(surf, color, pts, 2)
    elif name == "RHOMBUS":
        pts = [(cx, cy-s), (cx+s, cy), (cx, cy+s), (cx-s, cy)]
        pygame.draw.polygon(surf, color, pts, 2)
    elif name == "ERASER":
        r = pygame.Rect(cx-s, cy-s//2, size, size-4)
        pygame.draw.rect(surf, (220, 100, 120), r, border_radius=3)
        pygame.draw.rect(surf, color, r, 2, border_radius=3)
    elif name == "FILL":
        # Bucket icon
        pygame.draw.polygon(surf, color, [(cx-s, cy+s), (cx+s, cy+s),
                                           (cx+s, cy-s+4), (cx, cy-s)], 2)
        pygame.draw.circle(surf, color, (cx-s+2, cy+s-2), 2)
    elif name == "TEXT":
        f = pygame.font.Font(None, size + 8)
        t = f.render("T", True, color)
        surf.blit(t, (cx - t.get_width()//2, cy - t.get_height()//2))


# ───────────────────────────────────────────────────────────────────────────────
# Toolbar
# ───────────────────────────────────────────────────────────────────────────────

class Toolbar:
    PAD       = 6
    SWATCH_SZ = 15
    SWATCH_GAP= 2
    CELL_W    = 55
    CELL_H    = 46

    def __init__(self, x: int, total_h: int):
        self.x = x
        self.w = TOOLBAR_W
        self.h = total_h
        self.font_big  = load_font(18, bold=True)
        self.font_med  = load_font(13, bold=True)
        self.font_tiny = load_font(10)

        self._tool_rects: dict[str, pygame.Rect] = {}
        self._size_rects: list[pygame.Rect] = []
        self._fill_rect   = pygame.Rect(0, 0, 0, 0)
        self._swatch_rects: list[tuple[pygame.Rect, tuple]] = []
        self._layout()

    def _layout(self):
        p  = self.PAD
        x  = self.x + p
        w  = self.w - p * 2
        y  = p + 18    # below "PAINT" title

        # Tool grid (2 columns)
        col_w = (w - 2) // 2
        for i, (name, _) in enumerate(TOOL_GRID):
            col = i % 2
            row = i // 2
            rx  = x + col * (col_w + 2)
            ry  = y + row * (self.CELL_H + 3)
            r   = pygame.Rect(rx, ry, col_w, self.CELL_H)
            if name:
                self._tool_rects[name] = r

        y += (len(TOOL_GRID) // 2) * (self.CELL_H + 3) + 6

        # Brush size buttons (3 across)
        sz_w = (w - 4) // 3
        for i in range(3):
            r = pygame.Rect(x + i*(sz_w+2), y, sz_w, 22)
            self._size_rects.append(r)
        y += 28

        # Fill toggle
        self._fill_rect = pygame.Rect(x, y, w, 22)
        y += 28

        # Palette swatches (4 columns)
        cols = 4
        sz   = self.SWATCH_SZ
        gap  = self.SWATCH_GAP
        col_space = sz + gap
        for i, color in enumerate(PALETTE):
            col = i % cols
            row = i // cols
            sx  = x + col * col_space
            sy  = y + row * col_space
            self._swatch_rects.append((pygame.Rect(sx, sy, sz, sz), color))

    # ── Hit tests ─────────────────────────────────────────────────────────────

    def hit_tool(self, pos) -> str | None:
        for name, rect in self._tool_rects.items():
            if rect.collidepoint(pos):
                return name
        return None

    def hit_size(self, pos) -> int | None:
        for i, r in enumerate(self._size_rects):
            if r.collidepoint(pos):
                return i        # 0=small, 1=medium, 2=large
        return None

    def hit_fill_toggle(self, pos) -> bool:
        return self._fill_rect.collidepoint(pos)

    def hit_swatch(self, pos) -> tuple | None:
        for rect, color in self._swatch_rects:
            if rect.collidepoint(pos):
                return color
        return None

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf, active_tool, active_color, brush_idx, filled, mouse_pos):
        pygame.draw.rect(surf, C_TOOLBAR_BG, (self.x, 0, self.w, self.h))
        pygame.draw.line(surf, C_TOOLBAR_EDGE, (self.x, 0), (self.x, self.h), 2)

        p = self.PAD
        x = self.x + p

        # Title
        title = self.font_med.render("PAINT", True, C_TOOL_ACTIVE)
        surf.blit(title, (self.x + (self.w - title.get_width())//2, p))

        # Tool buttons
        for name, (_, shortcut) in zip(
            [n for n, _ in TOOL_GRID if n], 
            [(n, s) for n, s in TOOL_GRID if n]
        ):
            rect      = self._tool_rects[name]
            is_active = (name == active_tool)
            is_hover  = rect.collidepoint(mouse_pos) and not is_active
            bg = C_TOOL_ACTIVE if is_active else (C_TOOL_HOVER if is_hover else C_TOOL_NORMAL)
            rr(surf, bg, rect, radius=5)
            rr(surf, C_TOOL_BORDER, rect, radius=5, width=1)

            icon_color = (255, 255, 255) if is_active else C_TEXT
            draw_tool_icon(surf, name, rect.centerx, rect.y + 16, icon_color, size=14)

            lbl = self.font_tiny.render(name[:6], True,
                                        C_TEXT if is_active else C_TEXT_DIM)
            surf.blit(lbl, (rect.centerx - lbl.get_width()//2, rect.bottom - 12))

        # Brush size buttons
        labels = ["S(1)", "M(2)", "L(3)"]
        for i, (r, lbl_str) in enumerate(zip(self._size_rects, labels)):
            is_active = (i == brush_idx)
            is_hover  = r.collidepoint(mouse_pos) and not is_active
            bg = C_TOOL_ACTIVE if is_active else (C_TOOL_HOVER if is_hover else C_TOOL_NORMAL)
            rr(surf, bg, r, radius=4)
            rr(surf, C_TOOL_BORDER, r, radius=4, width=1)
            lbl = self.font_tiny.render(lbl_str, True, C_TEXT if is_active else C_TEXT_DIM)
            surf.blit(lbl, (r.centerx - lbl.get_width()//2, r.centery - lbl.get_height()//2))

        # Fill toggle
        fr = self._fill_rect
        fhov = fr.collidepoint(mouse_pos)
        rr(surf, C_TOOL_HOVER if fhov else C_TOOL_NORMAL, fr, 4)
        rr(surf, C_TOOL_BORDER, fr, 4, width=1)
        fl = self.font_tiny.render("FILL ✓" if filled else "FILL ✗", True,
                                    C_TOOL_ACTIVE if filled else C_TEXT_DIM)
        surf.blit(fl, (fr.centerx - fl.get_width()//2, fr.centery - fl.get_height()//2))

        # Palette swatches
        for rect, color in self._swatch_rects:
            pygame.draw.rect(surf, color, rect)
            if color == active_color:
                pygame.draw.rect(surf, (255, 255, 255), rect, 2)
            else:
                pygame.draw.rect(surf, C_TOOLBAR_BG, rect, 1)

        # Big active-color swatch at bottom
        bot_y = self.h - 38
        big   = pygame.Rect(x, bot_y, self.w - p*2, 24)
        pygame.draw.rect(surf, active_color, big, border_radius=4)
        pygame.draw.rect(surf, C_TOOL_BORDER, big, 1, border_radius=4)
        cl = self.font_tiny.render("COLOR", True, C_TEXT_DIM)
        surf.blit(cl, (self.x + (self.w - cl.get_width())//2, bot_y - 12))


# ───────────────────────────────────────────────────────────────────────────────
# Canvas
# ───────────────────────────────────────────────────────────────────────────────

class Canvas:
    MAX_UNDO = 20

    def __init__(self, w: int, h: int, offset_x: int = 0):
        self.w  = w
        self.h  = h
        self.ox = offset_x
        self.surf = pygame.Surface((w, h))
        self.bg   = checkerboard(w, h)
        self.surf.blit(self.bg, (0, 0))
        self._history: list[pygame.Surface] = [self.surf.copy()]

    # ── History ───────────────────────────────────────────────────────────────

    def commit(self):
        snap = self.surf.copy()
        self._history.append(snap)
        if len(self._history) > self.MAX_UNDO:
            self._history.pop(0)

    def undo(self):
        if len(self._history) > 1:
            self._history.pop()
            self.surf.blit(self._history[-1], (0, 0))

    # ── Coordinates ───────────────────────────────────────────────────────────

    def to_local(self, screen_pos) -> tuple[int, int]:
        return (screen_pos[0] - self.ox, screen_pos[1])

    def in_bounds(self, local_pos) -> bool:
        return 0 <= local_pos[0] < self.w and 0 <= local_pos[1] < self.h

    # ── Primitives ────────────────────────────────────────────────────────────

    def draw_pencil(self, p1, p2, color, size):
        pygame.draw.line(self.surf, color, p1, p2, max(1, size))
        pygame.draw.circle(self.surf, color, p2, size // 2)

    def erase(self, p1, p2, size):
        er = max(1, size)
        self.surf.blit(self.bg,
                       (min(p1[0], p2[0]) - er - 2, min(p1[1], p2[1]) - er - 2),
                       pygame.Rect(min(p1[0], p2[0]) - er - 2,
                                   min(p1[1], p2[1]) - er - 2,
                                   abs(p2[0]-p1[0]) + er*2 + 4,
                                   abs(p2[1]-p1[1]) + er*2 + 4))
        pygame.draw.line(self.surf, C_CANVAS_BG, p1, p2, er)
        pygame.draw.circle(self.surf, C_CANVAS_BG, p2, er // 2)
        # Re-stamp background texture under erased area
        mask_r = pygame.Rect(
            min(p1[0], p2[0]) - er - 2,
            min(p1[1], p2[1]) - er - 2,
            abs(p2[0] - p1[0]) + er * 2 + 4,
            abs(p2[1] - p1[1]) + er * 2 + 4
        ).clamp(self.surf.get_rect())
        self.surf.blit(self.bg, mask_r.topleft, mask_r)

    def do_fill(self, local_pos, color):
        flood_fill(self.surf, local_pos, color)

    def draw_committed_shape(self, tool, p1, p2, color, filled, width):
        draw_shape(self.surf, tool, p1, p2, color, filled, width)

    def render_text(self, text: str, pos, color, font: pygame.font.Font):
        ts = font.render(text, True, color)
        self.surf.blit(ts, pos)

    def clear(self):
        self.surf.blit(self.bg, (0, 0))
        self.commit()

    def pick_color(self, local_pos) -> tuple:
        if self.in_bounds(local_pos):
            return self.surf.get_at(local_pos)[:3]
        return (0, 0, 0)

    def save(self) -> str:
        fn = f"paint_{timestamp()}.png"
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), fn)
        pygame.image.save(self.surf, path)
        return path

    def blit_to(self, target):
        target.blit(self.surf, (self.ox, 0))


# ───────────────────────────────────────────────────────────────────────────────
# Shape / Line preview overlay
# ───────────────────────────────────────────────────────────────────────────────

class ShapePreview:
    """Ghost preview drawn on screen (alpha) while dragging."""

    def __init__(self):
        self.active = False
        self.tool   = None
        self.p1     = (0, 0)
        self.p2     = (0, 0)
        self.color  = (0, 0, 0)
        self.filled = False
        self.width  = 2

    def start(self, tool, p1, color, filled, width):
        self.active = True
        self.tool   = tool
        self.p1 = self.p2 = p1
        self.color  = color
        self.filled = filled
        self.width  = width

    def update(self, p2):
        self.p2 = p2

    def stop(self):
        self.active = False

    def _ghost(self) -> tuple:
        return self.color + (130,)

    def draw(self, surf):
        if not self.active:
            return
        p1, p2 = self.p1, self.p2

        if self.tool == "LINE":
            pygame.draw.line(surf, self._ghost(), p1, p2, max(1, self.width))
            for pt in (p1, p2):
                pygame.draw.circle(surf, (255, 255, 255), pt, 4)
                pygame.draw.circle(surf, self.color, pt, 4, 1)

        elif self.tool in {"RECT", "SQUARE"}:
            r = (rect_from_two_points(p1, p2)
                 if self.tool == "RECT"
                 else square_from_two_points(p1, p2))
            if r.width < 1 or r.height < 1:
                return
            tmp = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
            if self.filled:
                tmp.fill(self._ghost())
            else:
                pygame.draw.rect(tmp, self._ghost(), tmp.get_rect(), max(1, self.width))
            surf.blit(tmp, r.topleft)

        elif self.tool == "CIRCLE":
            center, radius = circle_from_two_points(p1, p2)
            if radius < 1:
                return
            tmp = pygame.Surface((radius*2+4, radius*2+4), pygame.SRCALPHA)
            cc = (radius+2, radius+2)
            lw = 0 if self.filled else max(1, self.width)
            pygame.draw.circle(tmp, self._ghost(), cc, radius, lw)
            surf.blit(tmp, (center[0]-radius-2, center[1]-radius-2))
            pygame.draw.line(surf, (255,255,255), center, p2, 1)

        elif self.tool in POLY_TOOLS:
            if self.tool == "RTRI":
                pts = right_triangle_points(p1, p2)
            elif self.tool == "EQTRI":
                pts = equilateral_triangle_points(p1, p2)
            else:
                pts = rhombus_points(p1, p2)
            ipts = [(int(x), int(y)) for x, y in pts]
            # Draw on alpha surface
            xs = [x for x,y in ipts]; ys = [y for x,y in ipts]
            ox2 = min(xs); oy2 = min(ys)
            w2 = max(xs)-ox2+1; h2 = max(ys)-oy2+1
            if w2 < 1 or h2 < 1:
                return
            tmp = pygame.Surface((w2, h2), pygame.SRCALPHA)
            shifted = [(x-ox2, y-oy2) for x,y in ipts]
            lw = 0 if self.filled else max(1, self.width)
            pygame.draw.polygon(tmp, self._ghost(), shifted, lw)
            surf.blit(tmp, (ox2, oy2))


# ───────────────────────────────────────────────────────────────────────────────
# Text input state
# ───────────────────────────────────────────────────────────────────────────────

class TextInput:
    """Manages in-progress text entry on the canvas."""

    def __init__(self):
        self.active   = False
        self.pos      = (0, 0)      # screen position where text starts
        self.text     = ""
        self.font     = None
        self.color    = (0, 0, 0)
        self._blink   = 0
        self._show_cursor = True

    def start(self, screen_pos, color, font):
        self.active   = True
        self.pos      = screen_pos
        self.text     = ""
        self.color    = color
        self.font     = font
        self._blink   = 0
        self._show_cursor = True

    def cancel(self):
        self.active = False
        self.text   = ""

    def add_char(self, ch: str):
        self.text += ch

    def backspace(self):
        self.text = self.text[:-1]

    def tick(self, dt_ms: int):
        """Call each frame with elapsed ms; toggles cursor blink."""
        self._blink += dt_ms
        if self._blink >= 530:
            self._blink = 0
            self._show_cursor = not self._show_cursor

    def draw_overlay(self, surf):
        """Draw live text + blinking cursor over the screen."""
        if not self.active or self.font is None:
            return
        rendered = self.font.render(self.text, True, self.color)
        # Shadow
        shadow = self.font.render(self.text, True, (200, 200, 200))
        surf.blit(shadow, (self.pos[0]+1, self.pos[1]+1))
        surf.blit(rendered, self.pos)
        # Cursor
        if self._show_cursor:
            cx = self.pos[0] + rendered.get_width() + 1
            pygame.draw.line(surf, C_TEXT_CURSOR,
                             (cx, self.pos[1]),
                             (cx, self.pos[1] + rendered.get_height()), 2)


# ───────────────────────────────────────────────────────────────────────────────
# Custom cursor
# ───────────────────────────────────────────────────────────────────────────────

def draw_cursor(surf, pos, tool, brush_size, color, on_canvas):
    x, y   = pos
    clen   = 10
    gap    = 4
    for arm in [(-clen,0,-gap,0),(gap,0,clen,0),(0,-clen,0,-gap),(0,gap,0,clen)]:
        x1,y1,x2,y2 = arm
        pygame.draw.line(surf,(255,255,255),(x+x1,y+y1),(x+x2,y+y2),3)
        pygame.draw.line(surf,(0,0,0),(x+x1,y+y1),(x+x2,y+y2),1)
    if on_canvas and tool in ("PENCIL", "ERASER"):
        r = max(2, brush_size // 2)
        c = color if tool == "PENCIL" else (180, 180, 180)
        pygame.draw.circle(surf, (255,255,255), (x,y), r+1, 2)
        pygame.draw.circle(surf, c,             (x,y), r+1, 1)


# ───────────────────────────────────────────────────────────────────────────────
# Status bar
# ───────────────────────────────────────────────────────────────────────────────

STATUS_HINT = "[P/L/R/O/Q/A/B/M/E/G/T] tool  [1/2/3] size  [F] fill  [C] clear  [^Z] undo  [^S] save"

def draw_status(surf, font, tool, color, brush_idx, filled, mouse_pos, canvas_offset):
    bar_h = 22
    bar_y = WINDOW_H - bar_h
    pygame.draw.rect(surf, C_TOOLBAR_BG, (canvas_offset, bar_y, CANVAS_W, bar_h))
    pygame.draw.line(surf, C_TOOLBAR_EDGE, (canvas_offset, bar_y), (WINDOW_W, bar_y))
    cx = mouse_pos[0] - canvas_offset
    cy = mouse_pos[1]
    sz = BRUSH_SIZES[brush_idx]
    parts = [f"Tool:{tool}", f"Size:{sz}px",
             f"Pos:({max(0,cx)},{max(0,cy)})",
             STATUS_HINT]
    if tool in SHAPE_TOOLS - {"LINE"}:
        parts.insert(3, "FILL" if filled else "OUTLINE")
    ts = font.render("  |  ".join(parts), True, C_TEXT_DIM)
    surf.blit(ts, (canvas_offset + 6, bar_y + 4))


# ───────────────────────────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    pygame.display.set_caption("Paint Extended — TSIS 2")
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock  = pygame.time.Clock()
    pygame.mouse.set_visible(False)

    font_status = load_font(11)
    font_text   = load_font(22)   # used for TEXT tool

    toolbar = Toolbar(x=0, total_h=WINDOW_H)
    canvas  = Canvas(w=CANVAS_W, h=CANVAS_H, offset_x=TOOLBAR_W)
    preview = ShapePreview()
    text_in = TextInput()

    # State
    active_tool  = "PENCIL"
    active_color = PALETTE[0]
    brush_idx    = 1           # 0=small, 1=medium, 2=large
    filled       = True
    drawing      = False
    last_pos     = None
    save_msg     = ""
    save_timer   = 0

    def brush_size() -> int:
        return BRUSH_SIZES[brush_idx]

    def cvs(screen_p):
        return canvas.to_local(screen_p)

    def commit_shape():
        p1l = cvs(preview.p1)
        p2l = cvs(preview.p2)
        canvas.draw_committed_shape(active_tool, p1l, p2l,
                                    active_color, filled, brush_size())
        canvas.commit()

    running = True
    while running:
        dt = clock.tick(FPS)
        text_in.tick(dt)

        mouse_pos   = pygame.mouse.get_pos()
        mouse_local = cvs(mouse_pos)
        on_canvas   = mouse_pos[0] >= TOOLBAR_W and mouse_pos[1] < CANVAS_H

        pressed   = pygame.key.get_pressed()
        ctrl_held = pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]

        for event in pygame.event.get():

            # ── Quit ──────────────────────────────────────────────────────
            if event.type == pygame.QUIT:
                running = False

            # ── KEY DOWN ──────────────────────────────────────────────────
            if event.type == pygame.KEYDOWN:

                # Text tool typing
                if text_in.active:
                    if event.key == pygame.K_RETURN:
                        # Commit text to canvas
                        local_pos = cvs(text_in.pos)
                        canvas.render_text(text_in.text, local_pos,
                                           text_in.color, text_in.font)
                        canvas.commit()
                        text_in.cancel()
                    elif event.key == pygame.K_ESCAPE:
                        text_in.cancel()
                    elif event.key == pygame.K_BACKSPACE:
                        text_in.backspace()
                    else:
                        if event.unicode and event.unicode.isprintable():
                            text_in.add_char(event.unicode)
                    continue   # all keys consumed by text input

                # Global quit
                if event.key == pygame.K_ESCAPE:
                    running = False

                # Ctrl shortcuts
                if ctrl_held:
                    if event.key == pygame.K_z:
                        canvas.undo()
                    elif event.key == pygame.K_s:
                        path = canvas.save()
                        save_msg   = f"Saved: {os.path.basename(path)}"
                        save_timer = 180   # frames to show message
                    continue

                # Tool select (letter keys)
                if event.key in KEY_TO_TOOL:
                    active_tool = KEY_TO_TOOL[event.key]

                # Brush size presets
                elif event.key == pygame.K_1:
                    brush_idx = 0
                elif event.key == pygame.K_2:
                    brush_idx = 1
                elif event.key == pygame.K_3:
                    brush_idx = 2

                # Fill toggle
                elif event.key == pygame.K_f:
                    filled = not filled

                # Fine brush size
                elif event.key == pygame.K_LEFTBRACKET:
                    BRUSH_SIZES[brush_idx] = max(1, BRUSH_SIZES[brush_idx] - 1)
                elif event.key == pygame.K_RIGHTBRACKET:
                    BRUSH_SIZES[brush_idx] = min(80, BRUSH_SIZES[brush_idx] + 1)

                # Clear
                elif event.key == pygame.K_c:
                    canvas.clear()

            # ── MOUSE BUTTON DOWN ─────────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN:
                if text_in.active:
                    # Clicking elsewhere cancels text
                    text_in.cancel()

                if event.button == 1:
                    if not on_canvas:
                        # Toolbar interactions
                        hit = toolbar.hit_tool(mouse_pos)
                        if hit:
                            active_tool = hit
                        elif (si := toolbar.hit_size(mouse_pos)) is not None:
                            brush_idx = si
                        elif toolbar.hit_fill_toggle(mouse_pos):
                            filled = not filled
                        else:
                            col = toolbar.hit_swatch(mouse_pos)
                            if col:
                                active_color = col
                        continue

                    # Canvas interactions
                    lp = mouse_local

                    if active_tool == "PENCIL":
                        drawing  = True
                        last_pos = lp
                        if canvas.in_bounds(lp):
                            pygame.draw.circle(canvas.surf, active_color,
                                               lp, brush_size() // 2)

                    elif active_tool == "ERASER":
                        drawing  = True
                        last_pos = lp
                        if canvas.in_bounds(lp):
                            canvas.erase(lp, lp, brush_size())

                    elif active_tool == "FILL":
                        if canvas.in_bounds(lp):
                            canvas.do_fill(lp, active_color)
                            canvas.commit()

                    elif active_tool == "TEXT":
                        text_in.start(mouse_pos, active_color, font_text)

                    elif active_tool in SHAPE_TOOLS:
                        drawing = True
                        preview.start(active_tool, mouse_pos, active_color,
                                      filled, brush_size())

            # ── MOUSE BUTTON UP ───────────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drawing:
                    drawing = False
                    if active_tool in SHAPE_TOOLS and preview.active:
                        commit_shape()
                        preview.stop()
                    elif active_tool in ("PENCIL", "ERASER"):
                        canvas.commit()
                    last_pos = None

            # ── MOUSE MOTION ──────────────────────────────────────────────
            if event.type == pygame.MOUSEMOTION and drawing:
                lp = mouse_local

                if active_tool == "PENCIL" and last_pos is not None:
                    if canvas.in_bounds(lp):
                        canvas.draw_pencil(last_pos, lp, active_color, brush_size())
                    last_pos = lp

                elif active_tool == "ERASER" and last_pos is not None:
                    if canvas.in_bounds(lp):
                        canvas.erase(last_pos, lp, brush_size())
                    last_pos = lp

                elif active_tool in SHAPE_TOOLS and preview.active:
                    preview.update(mouse_pos)

        # ── Render ──────────────────────────────────────────────────────────
        canvas.blit_to(screen)

        if preview.active:
            preview.draw(screen)

        text_in.draw_overlay(screen)

        toolbar.draw(screen, active_tool, active_color, brush_idx, filled, mouse_pos)

        draw_status(screen, font_status, active_tool, active_color,
                    brush_idx, filled, mouse_pos, TOOLBAR_W)

        # Save notification banner
        if save_timer > 0:
            save_timer -= 1
            alpha = min(255, save_timer * 4)
            msg_surf = font_status.render(save_msg, True, (80, 255, 120))
            bx = TOOLBAR_W + (CANVAS_W - msg_surf.get_width()) // 2
            pygame.draw.rect(screen, (20, 40, 20),
                             (bx - 8, 6, msg_surf.get_width() + 16, 20),
                             border_radius=4)
            screen.blit(msg_surf, (bx, 8))

        draw_cursor(screen, mouse_pos, active_tool, brush_size(),
                    active_color, on_canvas)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
