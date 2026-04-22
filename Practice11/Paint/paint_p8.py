"""
paint_p8.py — Paint Extended (Practice 8)
==========================================
Built on top of nerdparadise.com/programming/pygame/part6.
The original program let the user draw a freehand trail with the
mouse while switching between red / green / blue with R / G / B keys.

This version keeps that core idea and adds eight tools, a colour
palette, undo history, shape previews, and a retro pixel UI.

Tools
-----
  1  PENCIL      — freehand brush (original Part 6 mechanic)
  2  RECT        — axis-aligned rectangle  (drag corner → corner)
  3  CIRCLE      — circle by radius        (drag center → edge)
  4  ERASER      — erase back to canvas BG (variable size)
  5  SQUARE      — perfect square          (drag, side = min(Δx, Δy))
  6  R-TRI       — right triangle          (right angle at click point)
  7  EQ-TRI      — equilateral triangle    (horizontal base, apex up/down)
  8  RHOMBUS     — rhombus / diamond       (drag center → corner)

Keyboard shortcuts
------------------
  1–8        Select tool
  F          Toggle fill / outline for all polygon tools
  [ / ]      Decrease / Increase brush radius
  C          Clear canvas
  Ctrl+Z     Undo  (up to 20 steps)
  S          Save canvas as paint_save.png
  Esc        Quit

Mouse
-----
  Left click + drag   Draw
  Right click         Shrink brush radius (original Part 6 mechanic)
"""

import os
import math
import pygame


# ═══════════════════════════════════════════════════════════════════════════════
# Layout & sizing constants
# ═══════════════════════════════════════════════════════════════════════════════

CANVAS_W  = 780   # width of the drawable area in pixels
CANVAS_H  = 560   # height of the drawable area (includes 20px status bar)
TOOLBAR_W = 124   # width of the left-side tool panel
WINDOW_W  = CANVAS_W + TOOLBAR_W
WINDOW_H  = CANVAS_H
FPS       = 60    # target frames per second


# ═══════════════════════════════════════════════════════════════════════════════
# Colour palette  (PICO-8 / Commodore 64 inspired, 24 swatches)
# ═══════════════════════════════════════════════════════════════════════════════

PALETTE = [
    # Row 0 — greys / neutrals (dark → light)
    (0,   0,   0),   (29,  29,  29),  (73,  73,  73),
    (122, 122, 122), (179, 179, 179), (255, 255, 255),
    # Row 1 — warm hues (reds, oranges, yellows, greens)
    (190, 38,  51),  (224, 111, 139), (228, 166, 114),
    (254, 231, 97),  (99,  199, 77),  (62,  137, 72),
    # Row 2 — cool hues (teals, blues, purples, pinks)
    (36,  82,  59),  (0,   87,  132), (0,   149, 233),
    (154, 232, 254), (120, 70,  184), (215, 123, 186),
    # Row 3 — high-saturation accent colours
    (255, 0,   77),  (255, 163, 0),   (0,   255, 102),
    (41,  173, 255), (131, 118, 156), (194, 195, 199),
]


# ═══════════════════════════════════════════════════════════════════════════════
# UI colour tokens
# ═══════════════════════════════════════════════════════════════════════════════

C_TOOLBAR_BG  = (22,  18,  30)   # dark purple-black  — toolbar background
C_TOOLBAR_EDGE= (60,  50,  80)   # slightly lighter   — separator line
C_TOOL_NORMAL = (38,  32,  52)   # dark purple        — idle button
C_TOOL_HOVER  = (58,  50,  78)   # mid purple         — hovered button
C_TOOL_ACTIVE = (108, 82, 180)   # bright purple      — selected button
C_TOOL_BORDER = (80,  65, 110)   # border tint        — button outline
C_TEXT        = (245, 238, 255)  # near-white         — primary labels
C_TEXT_DIM    = (175, 165, 200)  # muted lavender     — secondary labels
C_CANVAS_BG   = (245, 242, 235)  # warm off-white     — canvas background


# ═══════════════════════════════════════════════════════════════════════════════
# Tool registry
# Tools are referenced by short string keys throughout the code.
# Adding a new tool requires: adding it here, drawing its icon in
# draw_tool_icon(), adding geometry in Canvas, and wiring it in main().
# ═══════════════════════════════════════════════════════════════════════════════

# Ordered list of all tool names — controls toolbar display order
TOOL_NAMES = ["PENCIL", "RECT", "CIRCLE", "ERASER",
              "SQUARE", "R-TRI", "EQ-TRI", "RHOMBUS"]

# Map keyboard keys (1–8) to tool names
TOOL_KEYS = {
    pygame.K_1: "PENCIL",
    pygame.K_2: "RECT",
    pygame.K_3: "CIRCLE",
    pygame.K_4: "ERASER",
    pygame.K_5: "SQUARE",
    pygame.K_6: "R-TRI",
    pygame.K_7: "EQ-TRI",
    pygame.K_8: "RHOMBUS",
}

# Tools that use a click-drag shape preview (not freehand)
SHAPE_TOOLS = {"RECT", "CIRCLE", "SQUARE", "R-TRI", "EQ-TRI", "RHOMBUS"}

# Tools that respect the fill / outline toggle
FILLABLE_TOOLS = {"RECT", "CIRCLE", "SQUARE", "R-TRI", "EQ-TRI", "RHOMBUS"}


# ═══════════════════════════════════════════════════════════════════════════════
# Geometry helpers
# ═══════════════════════════════════════════════════════════════════════════════

def rect_from_two_points(p1, p2) -> pygame.Rect:
    """Return a normalised Rect from any two corner points."""
    x = min(p1[0], p2[0])
    y = min(p1[1], p2[1])
    w = abs(p2[0] - p1[0])
    h = abs(p2[1] - p1[1])
    return pygame.Rect(x, y, w, h)


def square_from_two_points(p1, p2) -> pygame.Rect:
    """
    Return a square Rect whose corner is at p1.
    Side length = min(|Δx|, |Δy|) so the shape stays square while dragging.
    The direction (left/right, up/down) follows the drag direction.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    side = min(abs(dx), abs(dy))          # constrain to the smaller axis
    sx = p1[0] if dx >= 0 else p1[0] - side
    sy = p1[1] if dy >= 0 else p1[1] - side
    return pygame.Rect(sx, sy, side, side)


def right_triangle_points(p1, p2) -> list[tuple[int, int]]:
    """
    Return the three vertices of a right triangle.
    The right angle is placed at p1.
    One leg runs horizontally to (p2.x, p1.y).
    The other leg runs vertically from p1 to (p1.x, p2.y).

        p1 ──────── (p2.x, p1.y)
        │            /
        │           /
    (p1.x, p2.y)  ← this vertex is NOT used; the hypotenuse connects
                    (p2.x, p1.y) → (p1.x, p2.y) directly, forming
                    the right angle at p1.

    Vertices (clockwise): p1, (p2[0], p1[1]), (p1[0], p2[1])
    """
    x1, y1 = p1
    x2, y2 = p2
    return [(x1, y1), (x2, y1), (x1, y2)]


def equilateral_triangle_points(p1, p2) -> list[tuple[int, int]]:
    """
    Return three vertices of an equilateral triangle.
    p1 and p2 define the two base corners (drag = base width).
    The apex is centred above the base at height = side × (√3 / 2).
    The apex goes in the direction opposite to the drag (above if dragging right).
    """
    x1, y1 = p1
    x2, y2 = p2

    # Base length and midpoint
    base = math.hypot(x2 - x1, y2 - y1)
    if base < 1:
        return [p1, p2, p1]   # degenerate — no visible shape yet

    # Unit vector along the base
    bx = (x2 - x1) / base
    by = (y2 - y1) / base

    # Perpendicular unit vector (rotated 90° counter-clockwise)
    px, py = -by, bx

    # Apex height for equilateral triangle
    h = base * math.sqrt(3) / 2

    # Apex sits at the midpoint of the base displaced by h in the perp direction
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    ax = int(mx + px * h)
    ay = int(my + py * h)

    return [(x1, y1), (x2, y2), (ax, ay)]


def rhombus_points(p1, p2) -> list[tuple[int, int]]:
    """
    Return four vertices of a rhombus (diamond).
    p1 is the centre; p2 is dragged to define one corner.
    The half-diagonals are (Δx, 0) and (0, Δy), giving four points:
        top, right, bottom, left.
    """
    cx, cy = p1
    dx = abs(p2[0] - cx)   # horizontal half-diagonal
    dy = abs(p2[1] - cy)   # vertical half-diagonal
    return [
        (cx,      cy - dy),  # top
        (cx + dx, cy),       # right
        (cx,      cy + dy),  # bottom
        (cx - dx, cy),       # left
    ]


def circle_from_two_points(p1, p2) -> tuple[tuple[int, int], int]:
    """
    Return (centre, radius) for a circle.
    p1 = centre (click), p2 = any edge point (drag).
    """
    cx, cy = p1
    r = int(math.hypot(p2[0] - cx, p2[1] - cy))
    return (cx, cy), r


# ═══════════════════════════════════════════════════════════════════════════════
# Font loader  (falls back gracefully when Courier New isn't installed)
# ═══════════════════════════════════════════════════════════════════════════════

def load_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Try to load a monospace system font; fall back to pygame's built-in."""
    for name in ("Courier New", "Courier", "monospace", None):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)


# ═══════════════════════════════════════════════════════════════════════════════
# Drawing helpers
# ═══════════════════════════════════════════════════════════════════════════════

def draw_rounded_rect(surf, color, rect, radius: int = 6, width: int = 0):
    """Thin wrapper around pygame.draw.rect that always applies border_radius."""
    pygame.draw.rect(surf, color, rect, width, border_radius=radius)


def draw_tool_icon(surf, name: str, cx: int, cy: int,
                   color, size: int = 14):
    """
    Draw a small geometric icon representing each tool.
    Icons are built from pygame.draw primitives so they render correctly
    on every system regardless of which fonts are installed.

    Parameters
    ----------
    surf  : target Surface
    name  : tool name string (must be in TOOL_NAMES)
    cx,cy : centre coordinates for the icon
    color : primary icon colour
    size  : approximate bounding box half-size in pixels
    """
    s = size // 2  # half-size shorthand

    if name == "PENCIL":
        # Diagonal pencil body (parallelogram) with a yellow tip triangle
        body = [
            (cx - s,     cy + s),
            (cx - s + 4, cy + s),
            (cx + s,     cy - s + 4),
            (cx + s,     cy - s),
            (cx + s - 4, cy - s),
            (cx - s,     cy + s - 4),
        ]
        pygame.draw.polygon(surf, color, body)
        tip = [(cx - s, cy + s), (cx - s + 4, cy + s), (cx - s, cy + s - 4)]
        pygame.draw.polygon(surf, (255, 220, 60), tip)

    elif name == "RECT":
        # Simple outlined rectangle
        r = pygame.Rect(cx - s, cy - s + 2, size, size - 4)
        pygame.draw.rect(surf, color, r, 2, border_radius=1)

    elif name == "CIRCLE":
        # Simple outlined circle
        pygame.draw.circle(surf, color, (cx, cy), s, 2)

    elif name == "ERASER":
        # Pink block with a lighter left stripe (classic eraser look)
        r = pygame.Rect(cx - s, cy - s // 2, size, size - 4)
        pygame.draw.rect(surf, (210, 90, 110), r, border_radius=2)
        pygame.draw.rect(surf, color, r, 2, border_radius=2)
        stripe = pygame.Rect(cx - s, cy - s // 2, 5, size - 4)
        pygame.draw.rect(surf, (240, 190, 200), stripe,
                         border_top_left_radius=2, border_bottom_left_radius=2)

    elif name == "SQUARE":
        # Outlined square (perfectly equal sides)
        r = pygame.Rect(cx - s + 1, cy - s + 1, size - 2, size - 2)
        pygame.draw.rect(surf, color, r, 2)

    elif name == "R-TRI":
        # Right triangle — right angle at bottom-left
        pts = [(cx - s, cy + s), (cx + s, cy + s), (cx - s, cy - s)]
        pygame.draw.polygon(surf, color, pts, 2)
        # Small square in the corner to indicate the right angle
        sq = 4
        pygame.draw.lines(surf, color, False,
                          [(cx - s + sq, cy + s),
                           (cx - s + sq, cy + s - sq),
                           (cx - s,      cy + s - sq)], 1)

    elif name == "EQ-TRI":
        # Equilateral triangle pointing upward
        h = int(size * math.sqrt(3) / 2)
        pts = [(cx - s, cy + h // 2), (cx + s, cy + h // 2), (cx, cy - h // 2)]
        pygame.draw.polygon(surf, color, pts, 2)

    elif name == "RHOMBUS":
        # Diamond / rhombus shape
        pts = [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]
        pygame.draw.polygon(surf, color, pts, 2)


def checkerboard(w: int, h: int, tile: int = 12) -> pygame.Surface:
    """
    Generate a two-tone checkerboard Surface used as the canvas background.
    This gives a subtle texture that makes it obvious the canvas is empty
    and helps judge brush strokes near the edges.
    """
    surf = pygame.Surface((w, h))
    c1 = (245, 242, 235)   # warm white
    c2 = (225, 220, 210)   # warm light grey
    for row in range(h // tile + 1):
        for col in range(w // tile + 1):
            color = c1 if (row + col) % 2 == 0 else c2
            pygame.draw.rect(surf, color, (col * tile, row * tile, tile, tile))
    return surf


# ═══════════════════════════════════════════════════════════════════════════════
# Canvas  — manages the drawable Surface and undo history
# ═══════════════════════════════════════════════════════════════════════════════

class Canvas:
    """
    Wraps a pygame.Surface that the user paints on.

    Responsibilities
    ----------------
    - Hold and render the pixel data.
    - Provide typed drawing methods for every tool.
    - Maintain an undo stack (up to MAX_UNDO snapshots).
    - Map between screen coordinates and local canvas coordinates.
    """

    MAX_UNDO = 20   # maximum number of undo steps stored in memory

    def __init__(self, w: int, h: int, offset_x: int = 0):
        """
        Parameters
        ----------
        w, h      : canvas dimensions in pixels
        offset_x  : horizontal offset from the left edge of the window
                    (used to convert screen → local coordinates)
        """
        self.w   = w
        self.h   = h
        self.ox  = offset_x   # screen-space x offset (toolbar width)

        # The main drawable surface
        self.surf = pygame.Surface((w, h))

        # Pre-rendered background — blit this to "erase" regions
        self.bg = checkerboard(w, h)
        self.surf.blit(self.bg, (0, 0))

        # Undo history: list of Surface snapshots
        self._history: list[pygame.Surface] = []
        self._push_history()   # save the blank initial state

    # ── Undo history ──────────────────────────────────────────────────────────

    def _push_history(self):
        """Take a snapshot of the current canvas and append it to the stack."""
        snap = self.surf.copy()
        self._history.append(snap)
        # Trim the oldest entry when the stack overflows
        if len(self._history) > self.MAX_UNDO:
            self._history.pop(0)

    def commit(self):
        """Call this after finishing any stroke or shape to save an undo point."""
        self._push_history()

    def undo(self):
        """
        Restore the previous canvas state.
        If there is only one snapshot (the initial blank), do nothing.
        """
        if len(self._history) > 1:
            self._history.pop()                   # discard current state
            self.surf.blit(self._history[-1], (0, 0))  # restore previous

    # ── Coordinate helpers ────────────────────────────────────────────────────

    def to_local(self, screen_pos) -> tuple[int, int]:
        """Convert a screen-space position to canvas-local coordinates."""
        return (screen_pos[0] - self.ox, screen_pos[1])

    def in_bounds(self, local_pos) -> bool:
        """Return True if the local position lies within the canvas rectangle."""
        return 0 <= local_pos[0] < self.w and 0 <= local_pos[1] < self.h

    # ── Drawing primitives ────────────────────────────────────────────────────

    def draw_pencil(self, p1, p2, color, radius: int):
        """
        Draw a continuous freehand stroke between p1 and p2.
        A filled circle at p2 caps the stroke so there are no gaps
        even when the mouse moves fast.
        """
        pygame.draw.line(self.surf, color, p1, p2, max(1, radius * 2))
        pygame.draw.circle(self.surf, color, p2, radius)

    def draw_rect(self, p1, p2, color, filled: bool):
        """Draw an axis-aligned rectangle from corner p1 to corner p2."""
        r = rect_from_two_points(p1, p2)
        if r.width < 1 or r.height < 1:
            return
        width = 0 if filled else 2   # 0 = filled in pygame convention
        pygame.draw.rect(self.surf, color, r, width)

    def draw_square(self, p1, p2, color, filled: bool):
        """
        Draw a perfect square.
        Side length is constrained to min(|Δx|, |Δy|) so it stays square
        regardless of the drag angle.
        """
        r = square_from_two_points(p1, p2)
        if r.width < 1:
            return
        width = 0 if filled else 2
        pygame.draw.rect(self.surf, color, r, width)

    def draw_circle(self, p1, p2, color, filled: bool):
        """
        Draw a circle.
        p1 is the centre (click point); p2 is any point on the edge (drag).
        """
        center, radius = circle_from_two_points(p1, p2)
        if radius < 1:
            return
        width = 0 if filled else 2
        pygame.draw.circle(self.surf, color, center, radius, width)

    def draw_right_triangle(self, p1, p2, color, filled: bool):
        """
        Draw a right triangle with the right angle at p1.
        The two legs are axis-aligned (one horizontal, one vertical).
        """
        pts = right_triangle_points(p1, p2)
        width = 0 if filled else 2
        pygame.draw.polygon(self.surf, color, pts, width)

    def draw_equilateral_triangle(self, p1, p2, color, filled: bool):
        """
        Draw an equilateral triangle.
        p1 and p2 are the two base corners; the apex is computed so all
        three sides are equal length.
        """
        pts = equilateral_triangle_points(p1, p2)
        width = 0 if filled else 2
        pygame.draw.polygon(self.surf, color, pts, width)

    def draw_rhombus(self, p1, p2, color, filled: bool):
        """
        Draw a rhombus (diamond shape).
        p1 is the centre of the rhombus; p2 defines the reach of the
        diagonals — dx = |p2.x - p1.x|, dy = |p2.y - p1.y|.
        """
        pts = rhombus_points(p1, p2)
        width = 0 if filled else 2
        pygame.draw.polygon(self.surf, color, pts, width)

    def erase(self, p1, p2, radius: int):
        """
        Erase a stroke between p1 and p2 by stamping the background texture
        back onto the canvas.  This preserves the checkerboard pattern rather
        than leaving a flat-coloured smear.
        """
        er = max(1, radius * 2)
        # Paint a temporary flat path (using BG colour) as a clip mask
        pygame.draw.line(self.surf, C_CANVAS_BG, p1, p2, er)
        pygame.draw.circle(self.surf, C_CANVAS_BG, p2, radius)
        # Re-blit the matching region from the pre-rendered background
        mask_r = pygame.Rect(
            min(p1[0], p2[0]) - radius - 2,
            min(p1[1], p2[1]) - radius - 2,
            abs(p2[0] - p1[0]) + er + 4,
            abs(p2[1] - p1[1]) + er + 4,
        )
        mask_r.clamp_ip(self.surf.get_rect())
        self.surf.blit(self.bg, mask_r.topleft, mask_r)

    def clear(self):
        """Reset the canvas to the background and save an undo checkpoint."""
        self.surf.blit(self.bg, (0, 0))
        self.commit()

    def blit_to(self, target: pygame.Surface):
        """Composite the canvas onto another surface at the correct offset."""
        target.blit(self.surf, (self.ox, 0))


# ═══════════════════════════════════════════════════════════════════════════════
# ShapePreview — ghost overlay shown while the user drags a shape
# ═══════════════════════════════════════════════════════════════════════════════

class ShapePreview:
    """
    Renders a semi-transparent preview of the shape currently being dragged.
    The preview is drawn on top of the canvas (not committed to it) each frame
    using a temporary SRCALPHA surface so it doesn't permanently modify pixels.
    """

    def __init__(self):
        self.active = False
        self.tool   = None
        self.p1     = (0, 0)   # anchor point (screen coords, where drag started)
        self.p2     = (0, 0)   # current mouse position (screen coords)
        self.color  = (0, 0, 0)
        self.filled = False

    def start(self, tool: str, p1, color, filled: bool):
        """Begin a new preview drag."""
        self.active = True
        self.tool   = tool
        self.p1     = p1
        self.p2     = p1
        self.color  = color
        self.filled = filled

    def update(self, p2):
        """Update the current drag endpoint each frame."""
        self.p2 = p2

    def stop(self):
        """Hide the preview (called after the shape is committed)."""
        self.active = False

    def _ghost(self, alpha: int = 130) -> tuple:
        """Return the preview colour with transparency baked in."""
        return self.color + (alpha,)

    def draw(self, surf: pygame.Surface):
        """
        Render the ghost shape on *surf*.
        Each shape type computes its geometry (same helper functions as Canvas)
        and then draws onto a small SRCALPHA surface that is composited on top.
        """
        if not self.active:
            return

        ghost = self._ghost()
        p1, p2 = self.p1, self.p2

        if self.tool == "RECT":
            r = rect_from_two_points(p1, p2)
            self._draw_poly_ghost(surf, r, ghost, kind="rect")

        elif self.tool == "SQUARE":
            r = square_from_two_points(p1, p2)
            self._draw_poly_ghost(surf, r, ghost, kind="rect")

        elif self.tool == "CIRCLE":
            center, radius = circle_from_two_points(p1, p2)
            if radius < 1:
                return
            # Allocate a surface just big enough for the circle
            tmp_size = radius * 2 + 6
            tmp = pygame.Surface((tmp_size, tmp_size), pygame.SRCALPHA)
            cx = cy = tmp_size // 2
            if self.filled:
                pygame.draw.circle(tmp, ghost, (cx, cy), radius)
            else:
                pygame.draw.circle(tmp, ghost, (cx, cy), radius, 2)
            surf.blit(tmp, (center[0] - cx, center[1] - cy))
            # Radius guide line from centre to drag point
            pygame.draw.line(surf, (255, 255, 255), center, p2, 1)
            pygame.draw.circle(surf, (255, 255, 255), center, 4)
            pygame.draw.circle(surf, self.color, center, 4, 1)

        elif self.tool == "R-TRI":
            pts = right_triangle_points(p1, p2)
            self._draw_polygon_ghost(surf, pts, ghost)

        elif self.tool == "EQ-TRI":
            pts = equilateral_triangle_points(p1, p2)
            self._draw_polygon_ghost(surf, pts, ghost)

        elif self.tool == "RHOMBUS":
            pts = rhombus_points(p1, p2)
            self._draw_polygon_ghost(surf, pts, ghost)

        # Corner/vertex anchor dots to give tactile feedback
        if self.tool in ("RECT", "SQUARE"):
            for corner in (p1, p2,
                           (p1[0], p2[1]),
                           (p2[0], p1[1])):
                pygame.draw.circle(surf, (255, 255, 255), corner, 3)
                pygame.draw.circle(surf, self.color, corner, 3, 1)
        else:
            for pt in (p1, p2):
                pygame.draw.circle(surf, (255, 255, 255), pt, 3)
                pygame.draw.circle(surf, self.color, pt, 3, 1)

    def _draw_poly_ghost(self, surf, rect: pygame.Rect, ghost, kind: str):
        """Helper: draw a rect/square ghost on a temporary SRCALPHA surface."""
        if rect.width < 1 or rect.height < 1:
            return
        tmp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        if self.filled:
            tmp.fill(ghost)
        else:
            pygame.draw.rect(tmp, ghost, tmp.get_rect(), 2)
        surf.blit(tmp, rect.topleft)

    def _draw_polygon_ghost(self, surf, pts: list, ghost):
        """Helper: draw a polygon ghost on a temporary SRCALPHA surface."""
        if not pts:
            return
        # Bounding box of the polygon
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x0, y0 = min(xs) - 2, min(ys) - 2
        bw = max(xs) - x0 + 4
        bh = max(ys) - y0 + 4
        if bw < 1 or bh < 1:
            return
        tmp = pygame.Surface((bw, bh), pygame.SRCALPHA)
        local = [(p[0] - x0, p[1] - y0) for p in pts]
        if self.filled:
            pygame.draw.polygon(tmp, ghost, local)
        else:
            pygame.draw.polygon(tmp, ghost, local, 2)
        surf.blit(tmp, (x0, y0))


# ═══════════════════════════════════════════════════════════════════════════════
# Toolbar  — left-side tool panel with buttons, fill toggle, and colour palette
# ═══════════════════════════════════════════════════════════════════════════════

class Toolbar:
    """
    Renders and handles hit-testing for the left-side panel.

    Layout (top → bottom)
    ---------------------
      "PAINT" title
      8 tool buttons arranged in a 2×4 grid
      Fill / outline toggle button
      Brush radius preview + label
      24-colour palette swatches (3 columns)
      Active colour big swatch at the very bottom
    """

    PAD       = 7    # padding inside the toolbar panel
    SWATCH_SZ = 18   # palette swatch square size in pixels
    SWATCH_GAP= 3    # gap between swatches
    TOOL_H    = 44   # height of each tool button row
    RADIUS_H  = 34   # height of the radius preview widget

    def __init__(self, x: int, total_h: int):
        """
        Parameters
        ----------
        x       : left edge of the toolbar in screen coordinates
        total_h : full window height (toolbar fills it entirely)
        """
        self.x = x
        self.w = TOOLBAR_W
        self.h = total_h

        # Fonts at three sizes for the toolbar labels
        self.font_big  = load_font(18, bold=True)
        self.font_med  = load_font(13, bold=True)
        self.font_tiny = load_font(10)

        # Pre-computed click regions — populated by _layout()
        self._tool_rects:   dict[str, pygame.Rect]          = {}
        self._swatch_rects: list[tuple[pygame.Rect, tuple]] = []
        self._fill_rect   = pygame.Rect(0, 0, 0, 0)
        self._radius_rect = pygame.Rect(0, 0, 0, 0)
        self._layout()

    def _layout(self):
        """
        Pre-compute all widget rectangles.
        Called once during __init__; none of the rects change at runtime.
        """
        p  = self.PAD
        x0 = self.x + p          # left edge of widgets
        w  = self.w - p * 2      # usable widget width
        y  = p + 2               # current vertical cursor

        # ── Title label ──────────────────────────────────────────────
        y += 16   # space for "PAINT" text (drawn in draw(), not a Rect)

        # ── Tool buttons — 2 columns of 4 ───────────────────────────
        cols = 2
        btn_gap = 3
        btn_w = (w - btn_gap) // cols   # width of one button

        for i, name in enumerate(TOOL_NAMES):
            col = i % cols
            row = i // cols
            bx  = x0 + col * (btn_w + btn_gap)
            by  = y  + row * (self.TOOL_H + btn_gap)
            self._tool_rects[name] = pygame.Rect(bx, by, btn_w, self.TOOL_H)

        y += (len(TOOL_NAMES) // cols) * (self.TOOL_H + btn_gap) + 4

        # ── Fill toggle button ────────────────────────────────────────
        self._fill_rect = pygame.Rect(x0, y, w, 22)
        y += 26

        # ── Radius preview widget ─────────────────────────────────────
        self._radius_rect = pygame.Rect(x0, y, w, self.RADIUS_H)
        y += self.RADIUS_H + 8

        # ── Palette swatches — 3 columns ─────────────────────────────
        cols_sw = 3
        sz  = self.SWATCH_SZ
        gap = self.SWATCH_GAP
        for i, color in enumerate(PALETTE):
            col = i % cols_sw
            row = i // cols_sw
            sx  = x0 + col * (sz + gap)
            sy  = y  + row * (sz + gap)
            self._swatch_rects.append((pygame.Rect(sx, sy, sz, sz), color))

    # ── Hit-testing ───────────────────────────────────────────────────────────

    def hit_tool(self, pos) -> str | None:
        """Return the tool name if *pos* is inside a tool button, else None."""
        for name, rect in self._tool_rects.items():
            if rect.collidepoint(pos):
                return name
        return None

    def hit_fill_toggle(self, pos) -> bool:
        """Return True if *pos* is inside the fill/outline toggle button."""
        return self._fill_rect.collidepoint(pos)

    def hit_swatch(self, pos) -> tuple | None:
        """Return the RGB colour tuple if *pos* is inside a palette swatch."""
        for rect, color in self._swatch_rects:
            if rect.collidepoint(pos):
                return color
        return None

    # ── Rendering ─────────────────────────────────────────────────────────────

    def draw(self, surf: pygame.Surface, active_tool: str,
             active_color, radius: int, filled: bool, mouse_pos):
        """
        Render the entire toolbar onto *surf*.

        Parameters
        ----------
        active_tool  : currently selected tool name
        active_color : current drawing colour (RGB tuple)
        radius       : current brush radius in pixels
        filled       : whether shapes are drawn filled or outlined
        mouse_pos    : current mouse position (for hover effects)
        """

        # ── Background and edge line ──────────────────────────────────
        pygame.draw.rect(surf, C_TOOLBAR_BG, (self.x, 0, self.w, self.h))
        pygame.draw.line(surf, C_TOOLBAR_EDGE,
                         (self.x + self.w - 1, 0),
                         (self.x + self.w - 1, self.h), 2)

        # ── "PAINT" title ─────────────────────────────────────────────
        title = self.font_med.render("PAINT", True, C_TOOL_ACTIVE)
        surf.blit(title, (self.x + (self.w - title.get_width()) // 2,
                          self.PAD + 2))

        # ── Tool buttons ──────────────────────────────────────────────
        for name, rect in self._tool_rects.items():
            is_active = (name == active_tool)
            is_hover  = rect.collidepoint(mouse_pos) and not is_active

            # Background fill: active > hover > normal
            bg = (C_TOOL_ACTIVE if is_active
                  else C_TOOL_HOVER if is_hover
                  else C_TOOL_NORMAL)
            draw_rounded_rect(surf, bg, rect, radius=5)
            draw_rounded_rect(surf, C_TOOL_BORDER, rect, radius=5, width=1)

            # Geometric icon (white on active, C_TEXT otherwise)
            icon_col = (255, 255, 255) if is_active else C_TEXT
            draw_tool_icon(surf, name,
                           rect.centerx, rect.y + rect.height // 2 - 6,
                           icon_col, size=14)

            # Label below the icon
            label_col = C_TEXT if is_active else C_TEXT_DIM
            lbl = self.font_tiny.render(name, True, label_col)
            surf.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                            rect.bottom - lbl.get_height() - 2))

        # ── Fill / outline toggle ─────────────────────────────────────
        fr = self._fill_rect
        fhover = fr.collidepoint(mouse_pos)
        draw_rounded_rect(surf, C_TOOL_HOVER if fhover else C_TOOL_NORMAL, fr, 4)
        draw_rounded_rect(surf, C_TOOL_BORDER, fr, 4, width=1)
        fill_text = "[F] FILL" if filled else "[F] LINE"
        fc = C_TOOL_ACTIVE if filled else C_TEXT_DIM
        fl = self.font_tiny.render(fill_text, True, fc)
        surf.blit(fl, (fr.centerx - fl.get_width() // 2,
                       fr.centery - fl.get_height() // 2))

        # ── Radius preview ────────────────────────────────────────────
        rr = self._radius_rect
        draw_rounded_rect(surf, C_TOOL_NORMAL, rr, 4)
        draw_rounded_rect(surf, C_TOOL_BORDER, rr, 4, width=1)
        rl = self.font_tiny.render(f"sz:{radius}px", True, C_TEXT_DIM)
        surf.blit(rl, (rr.centerx - rl.get_width() // 2, rr.y + 3))
        # Small filled circle preview using the active colour
        dot_r = min(radius, 10)
        pygame.draw.circle(surf, active_color,
                           (rr.centerx, rr.y + 22), dot_r)

        # ── Palette swatches ──────────────────────────────────────────
        for rect, color in self._swatch_rects:
            pygame.draw.rect(surf, color, rect)
            if color == active_color:
                # Highlight the selected swatch with a white + black ring
                pygame.draw.rect(surf, (255, 255, 255), rect, 2)
                pygame.draw.rect(surf, (0,   0,   0),   rect, 1)
            else:
                pygame.draw.rect(surf, C_TOOLBAR_BG, rect, 1)

        # ── Active colour strip at the very bottom ────────────────────
        p = self.PAD
        bot_y = self.h - 36
        lbl_c = self.font_tiny.render("COLOR", True, C_TEXT_DIM)
        surf.blit(lbl_c, (self.x + (self.w - lbl_c.get_width()) // 2, bot_y - 11))
        big = pygame.Rect(self.x + p, bot_y, self.w - p * 2, 26)
        pygame.draw.rect(surf, active_color, big, border_radius=4)
        pygame.draw.rect(surf, C_TOOL_BORDER, big, 1, border_radius=4)


# ═══════════════════════════════════════════════════════════════════════════════
# Custom cursor
# ═══════════════════════════════════════════════════════════════════════════════

def draw_cursor(surf: pygame.Surface, pos, tool: str,
                radius: int, color, on_canvas: bool):
    """
    Draw a custom crosshair cursor that is visible on any background.

    Technique: each arm of the crosshair is drawn twice — first as a 3px
    white line (outline), then as a 1px black line on top — so the cursor
    contrasts against both light and dark pixels.

    When on the canvas:
      - Pencil: shows the brush-size circle so the user knows the paint radius.
      - Eraser: shows the eraser-size circle in grey.
    When on the toolbar:
      - Shows a small dot instead of the full crosshair.
    """
    x, y = pos
    clen  = 10   # length of each crosshair arm in pixels
    gap   = 3    # gap around the centre so the cursor tip is visible

    # Four arms: left, right, up, down — each as (dx1, dy1, dx2, dy2)
    arms = [
        (-clen, 0, -gap, 0),
        ( gap,  0,  clen, 0),
        (0, -clen, 0, -gap),
        (0,  gap,  0,  clen),
    ]
    for dx1, dy1, dx2, dy2 in arms:
        # White border (3px)
        pygame.draw.line(surf, (255, 255, 255),
                         (x + dx1, y + dy1), (x + dx2, y + dy2), 3)
        # Black centre (1px)
        pygame.draw.line(surf, (0, 0, 0),
                         (x + dx1, y + dy1), (x + dx2, y + dy2), 1)

    if on_canvas and tool == "PENCIL":
        # Brush-size preview circle — white halo + active colour ring
        pygame.draw.circle(surf, (255, 255, 255), (x, y), radius + 1, 2)
        pygame.draw.circle(surf, color,            (x, y), radius + 1, 1)

    elif on_canvas and tool == "ERASER":
        # Eraser-size preview circle in neutral grey
        pygame.draw.circle(surf, (255, 255, 255), (x, y), radius + 1, 2)
        pygame.draw.circle(surf, (160, 160, 160), (x, y), radius + 1, 1)

    elif not on_canvas:
        # On the toolbar: just a small dot to keep the cursor visible
        pygame.draw.circle(surf, (255, 255, 255), (x, y), 3, 2)
        pygame.draw.circle(surf, (0,   0,   0),   (x, y), 3, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# Status bar
# ═══════════════════════════════════════════════════════════════════════════════

def draw_status(surf: pygame.Surface, font, tool: str,
                radius: int, filled: bool, mouse_pos, canvas_offset: int):
    """
    Render a one-line status bar at the bottom of the window.
    Shows: active tool, brush size, canvas cursor position,
    fill mode (where applicable), and a compact key-binding reminder.
    """
    bar_h = 20
    bar_y = WINDOW_H - bar_h

    # Dark background strip
    pygame.draw.rect(surf, C_TOOLBAR_BG,
                     (canvas_offset, bar_y, CANVAS_W, bar_h))
    pygame.draw.line(surf, C_TOOLBAR_EDGE,
                     (canvas_offset, bar_y), (WINDOW_W, bar_y))

    # Canvas-local cursor coordinates
    cx = max(0, mouse_pos[0] - canvas_offset)
    cy = max(0, mouse_pos[1])

    parts = [
        f"Tool:{tool}",
        f"Size:{radius}px",
        f"({cx},{cy})",
    ]
    if tool in FILLABLE_TOOLS:
        parts.append("FILL" if filled else "LINE")
    parts.append("1-8:tool  F:fill  []:size  C:clear  Z:undo  S:save  Esc:quit")

    ts = font.render("  |  ".join(parts), True, C_TEXT_DIM)
    surf.blit(ts, (canvas_offset + 6, bar_y + 3))


# ═══════════════════════════════════════════════════════════════════════════════
# Main — application entry point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """
    Initialise pygame, create all objects, and run the main event loop.

    The loop follows the classic pygame pattern from nerdparadise Part 6:
      1. Poll events (keyboard, mouse buttons, mouse motion, quit).
      2. Update state (tool selection, drawing, undo, etc.).
      3. Render everything to the screen.
      4. Flip the display and wait for the next frame.
    """
    pygame.init()
    pygame.display.set_caption("Paint — Practice 8 Extended  |  pixel retro edition")
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock  = pygame.time.Clock()

    # Hide the OS cursor — we draw our own every frame
    pygame.mouse.set_visible(False)

    # Shared fonts
    font_status = load_font(11)

    # Core objects
    toolbar = Toolbar(x=0, total_h=WINDOW_H)
    canvas  = Canvas(w=CANVAS_W, h=CANVAS_H - 20, offset_x=TOOLBAR_W)
    preview = ShapePreview()

    # ── Application state ────────────────────────────────────────────────────
    active_tool  = "PENCIL"      # currently selected tool
    active_color = PALETTE[0]    # current drawing colour (starts black)
    radius       = 6             # pencil / eraser brush radius in pixels
    filled       = True          # True = filled shapes; False = outlined
    drawing      = False         # True while left mouse button is held down
    last_pos     = None          # previous mouse position for freehand tools

    # ── Inner helpers ────────────────────────────────────────────────────────

    def canvas_pos(screen_p) -> tuple[int, int]:
        """Convert a screen position to canvas-local coordinates."""
        return canvas.to_local(screen_p)

    def commit_shape():
        """
        Permanently write the previewed shape into the canvas Surface and
        push an undo snapshot.  Called when the mouse button is released.
        """
        p1l = canvas_pos(preview.p1)   # convert screen → canvas coordinates
        p2l = canvas_pos(preview.p2)

        if   active_tool == "RECT":
            canvas.draw_rect(p1l, p2l, active_color, filled)
        elif active_tool == "SQUARE":
            canvas.draw_square(p1l, p2l, active_color, filled)
        elif active_tool == "CIRCLE":
            canvas.draw_circle(p1l, p2l, active_color, filled)
        elif active_tool == "R-TRI":
            canvas.draw_right_triangle(p1l, p2l, active_color, filled)
        elif active_tool == "EQ-TRI":
            canvas.draw_equilateral_triangle(p1l, p2l, active_color, filled)
        elif active_tool == "RHOMBUS":
            canvas.draw_rhombus(p1l, p2l, active_color, filled)

        canvas.commit()   # save undo snapshot after shape is finalised

    # ── Main event loop ───────────────────────────────────────────────────────
    while True:
        mouse_pos   = pygame.mouse.get_pos()
        mouse_local = canvas_pos(mouse_pos)
        # True when the cursor is over the canvas (not the toolbar)
        on_canvas   = mouse_pos[0] >= TOOLBAR_W

        # Read held modifier keys once per frame
        pressed   = pygame.key.get_pressed()
        ctrl_held = pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]
        alt_held  = pressed[pygame.K_LALT]  or pressed[pygame.K_RALT]

        # ── Event processing ──────────────────────────────────────────────
        for event in pygame.event.get():

            # Quit: window X button, Ctrl+W, Alt+F4, or Escape
            if event.type == pygame.QUIT:
                pygame.quit(); return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); return
                if event.key == pygame.K_w and ctrl_held:
                    pygame.quit(); return
                if event.key == pygame.K_F4 and alt_held:
                    pygame.quit(); return

                # ── Tool selection (keys 1–8) ─────────────────────────
                if event.key in TOOL_KEYS:
                    active_tool = TOOL_KEYS[event.key]

                # ── Fill / outline toggle ─────────────────────────────
                elif event.key == pygame.K_f:
                    filled = not filled

                # ── Brush radius (square brackets) ────────────────────
                elif event.key == pygame.K_LEFTBRACKET:
                    radius = max(1, radius - 1)
                elif event.key == pygame.K_RIGHTBRACKET:
                    radius = min(60, radius + 1)

                # ── Clear canvas ──────────────────────────────────────
                elif event.key == pygame.K_c:
                    canvas.clear()

                # ── Undo (Ctrl+Z) ─────────────────────────────────────
                elif event.key == pygame.K_z and ctrl_held:
                    canvas.undo()

                # ── Save canvas as PNG ────────────────────────────────
                elif event.key == pygame.K_s:
                    save_path = os.path.join(
                        os.path.dirname(__file__), "paint_save.png")
                    pygame.image.save(canvas.surf, save_path)
                    print(f"[saved] {save_path}")

            # ── Mouse button DOWN ─────────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN:

                # Right click shrinks radius — Part 6 original mechanic
                if event.button == 3:
                    radius = max(1, radius - 1)
                    continue

                # Only handle left clicks from here
                if event.button != 1:
                    continue

                if not on_canvas:
                    # ── Toolbar interactions ──────────────────────────
                    hit = toolbar.hit_tool(mouse_pos)
                    if hit:
                        active_tool = hit
                    elif toolbar.hit_fill_toggle(mouse_pos):
                        filled = not filled
                    else:
                        col = toolbar.hit_swatch(mouse_pos)
                        if col:
                            active_color = col
                    continue

                # ── Start drawing on canvas ───────────────────────────
                drawing = True
                lp = mouse_local

                if active_tool == "PENCIL":
                    last_pos = lp
                    if canvas.in_bounds(lp):
                        # Draw an initial dot so a click without drag leaves a mark
                        pygame.draw.circle(canvas.surf, active_color, lp, radius)

                elif active_tool == "ERASER":
                    last_pos = lp
                    if canvas.in_bounds(lp):
                        canvas.erase(lp, lp, radius)

                elif active_tool in SHAPE_TOOLS:
                    # Begin the drag; preview starts at the click point
                    preview.start(active_tool, mouse_pos, active_color, filled)

            # ── Mouse button UP ───────────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and drawing:
                    drawing = False

                    if active_tool in SHAPE_TOOLS and preview.active:
                        # Finalise the shape and hide the preview
                        commit_shape()
                        preview.stop()

                    elif active_tool in ("PENCIL", "ERASER"):
                        # Save undo checkpoint when the stroke ends
                        canvas.commit()

                    last_pos = None

            # ── Mouse MOTION (while button is held) ───────────────────────
            if event.type == pygame.MOUSEMOTION and drawing:
                lp = mouse_local

                if active_tool == "PENCIL" and last_pos is not None:
                    # Connect previous and current positions with a thick line
                    if canvas.in_bounds(lp):
                        canvas.draw_pencil(last_pos, lp, active_color, radius)
                    last_pos = lp

                elif active_tool == "ERASER" and last_pos is not None:
                    if canvas.in_bounds(lp):
                        canvas.erase(last_pos, lp, radius)
                    last_pos = lp

                elif active_tool in SHAPE_TOOLS and preview.active:
                    # Update the ghost shape to follow the mouse
                    preview.update(mouse_pos)

        # ── Rendering ─────────────────────────────────────────────────────
        # 1. Canvas pixels (committed artwork)
        canvas.blit_to(screen)

        # 2. Shape preview ghost (rendered on top, not committed yet)
        if preview.active:
            preview.draw(screen)

        # 3. Toolbar panel (drawn over its own region)
        toolbar.draw(screen, active_tool, active_color, radius, filled, mouse_pos)

        # 4. Status bar (bottom strip of the canvas area)
        draw_status(screen, font_status, active_tool,
                    radius, filled, mouse_pos, TOOLBAR_W)

        # 5. Custom cursor (always last so it appears on top of everything)
        draw_cursor(screen, mouse_pos, active_tool, radius, active_color, on_canvas)

        # Flip the double buffer and wait until the next frame
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
