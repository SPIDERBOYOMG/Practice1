"""
Paint Extended — based on nerdparadise.com/programming/pygame/part6
===================================================================
Original: freehand trail drawing with R/G/B color modes.

New tools added
---------------
  [1] Pencil     — original freehand trail (from Part 6)
  [2] Rectangle  — click-drag to draw filled / outline rect
  [3] Circle     — click-drag to draw filled / outline circle
  [4] Eraser     — paints over with canvas color
  [5] Eyedropper — (bonus) pick any color from canvas

Keyboard shortcuts
------------------
  1-4       Select tool
  F         Toggle fill / outline for rect & circle
  [ / ]     Decrease / Increase brush radius
  C         Clear canvas
  S         Save screenshot (paint_save.png)
  Ctrl+Z    Undo (up to 20 steps)
  Escape    Quit

Mouse
-----
  Left click + drag   Draw / resize shape
  Right click         Shrink radius (original Part 6 mechanic)
"""

import sys
import os
import math
import pygame


# ───────────────────────────────────────────────────────────────────────────────
# Constants
# ───────────────────────────────────────────────────────────────────────────────

CANVAS_W, CANVAS_H = 800, 560
TOOLBAR_W          = 84        # left-side toolbar width
WINDOW_W           = CANVAS_W + TOOLBAR_W
WINDOW_H           = CANVAS_H
FPS                = 60

# Retro pixel palette ──────────────────────────────────────────────────────────
#  Inspired by PICO-8 / Commodore 64 / GameBoy palettes
PALETTE = [
    # Row 0 — darks & neutrals
    (0,   0,   0),    (29,  29,  29), (73,  73,  73),
    (122, 122, 122),  (179, 179, 179),(255, 255, 255),
    # Row 1 — reds / oranges
    (190, 38,  51),   (224, 111, 139),(228, 166, 114),
    (254, 231, 97),   (99,  199, 77), (62,  137, 72),
    # Row 2 — blues / purples
    (36,  82,  59),   (0,   87,  132),(0,   149, 233),
    (154, 232, 254),  (120, 70,  184),(215, 123, 186),
    # Row 3 — extra punchy
    (255, 0,   77),   (255, 163, 0),  (0,   255, 102),
    (41,  173, 255),  (131, 118, 156),(194, 195, 199),
]

# Toolbar colours ──────────────────────────────────────────────────────────────
C_TOOLBAR_BG   = (22,  18,  30)
C_TOOLBAR_EDGE = (60,  50,  80)
C_TOOL_NORMAL  = (38,  32,  52)
C_TOOL_HOVER   = (58,  50,  78)
C_TOOL_ACTIVE  = (108, 82, 180)
C_TOOL_BORDER  = (80,  65, 110)
C_TEXT         = (245, 238, 255)   # bright white-purple — readable on dark bg
C_TEXT_DIM     = (175, 165, 200)   # medium lavender — was too dark before
C_CANVAS_BG    = (245, 242, 235)   # warm off-white — classic paint canvas

TOOL_NAMES = ["PENCIL", "RECT", "CIRCLE", "ERASER"]
TOOL_ICONS = {}   # icons drawn via pygame.draw — see _draw_tool_icon()
TOOL_KEYS  = {
    pygame.K_1: "PENCIL",
    pygame.K_2: "RECT",
    pygame.K_3: "CIRCLE",
    pygame.K_4: "ERASER",
}


# ───────────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────────

def load_font(size: int, bold: bool = False):
    for name in ("Courier New", "Courier", "monospace", None):
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            return f
        except Exception:
            pass
    return pygame.font.Font(None, size)


def draw_rounded_rect(surf, color, rect, radius=6, width=0):
    pygame.draw.rect(surf, color, rect, width, border_radius=radius)




def draw_tool_icon(surf, name: str, cx: int, cy: int, color, size: int = 16):
    """Draw geometric icon for each tool — no emoji needed."""
    s = size // 2
    if name == "PENCIL":
        pts = [
            (cx - s,     cy + s),
            (cx - s + 4, cy + s),
            (cx + s,     cy - s + 4),
            (cx + s,     cy - s),
            (cx + s - 4, cy - s),
            (cx - s,     cy + s - 4),
        ]
        pygame.draw.polygon(surf, color, pts)
        tip = [(cx - s, cy + s), (cx - s + 4, cy + s), (cx - s, cy + s - 4)]
        pygame.draw.polygon(surf, (255, 220, 80), tip)
    elif name == "RECT":
        r = pygame.Rect(cx - s, cy - s + 2, size, size - 4)
        pygame.draw.rect(surf, color, r, 3, border_radius=2)
    elif name == "CIRCLE":
        pygame.draw.circle(surf, color, (cx, cy), s, 3)
    elif name == "ERASER":
        r = pygame.Rect(cx - s, cy - s // 2, size, size - 4)
        pygame.draw.rect(surf, (220, 100, 120), r, border_radius=3)
        pygame.draw.rect(surf, color, r, 2, border_radius=3)
        stripe = pygame.Rect(cx - s, cy - s // 2, 6, size - 4)
        pygame.draw.rect(surf, (240, 200, 210), stripe,
                         border_top_left_radius=3, border_bottom_left_radius=3)

def checkerboard(w: int, h: int, tile: int = 12):
    """Generate a checkerboard Surface (used as canvas BG)."""
    surf = pygame.Surface((w, h))
    c1, c2 = (245, 242, 235), (225, 220, 210)
    for row in range(h // tile + 1):
        for col in range(w // tile + 1):
            c = c1 if (row + col) % 2 == 0 else c2
            pygame.draw.rect(surf, c, (col * tile, row * tile, tile, tile))
    return surf


def rect_from_two_points(p1, p2):
    x = min(p1[0], p2[0])
    y = min(p1[1], p2[1])
    w = abs(p2[0] - p1[0])
    h = abs(p2[1] - p1[1])
    return pygame.Rect(x, y, w, h)


def circle_from_two_points(p1, p2):
    cx, cy = p1
    r = int(math.hypot(p2[0] - cx, p2[1] - cy))
    return (cx, cy), r


# ───────────────────────────────────────────────────────────────────────────────
# Toolbar
# ───────────────────────────────────────────────────────────────────────────────

class Toolbar:
    PAD       = 8
    SWATCH_SZ = 18    # palette swatch size
    SWATCH_GAP= 3
    TOOL_H    = 56
    RADIUS_H  = 36

    def __init__(self, x: int, total_h: int):
        self.x = x
        self.w = TOOLBAR_W
        self.h = total_h
        self.font_big  = load_font(22, bold=True)
        self.font_med  = load_font(14, bold=True)
        self.font_tiny = load_font(11)

        # Layout regions computed once
        self._tool_rects: dict[str, pygame.Rect] = {}
        self._swatch_rects: list[tuple[pygame.Rect, tuple]] = []
        self._fill_rect   = pygame.Rect(0, 0, 0, 0)
        self._radius_rect = pygame.Rect(0, 0, 0, 0)
        self._layout()

    def _layout(self):
        p   = self.PAD
        x   = self.x + p
        w   = self.w - p * 2
        y   = p + 10

        # Title height
        y += 20     # "PAINT" label

        # Tool buttons
        for name in TOOL_NAMES:
            r = pygame.Rect(x, y, w, self.TOOL_H)
            self._tool_rects[name] = r
            y += self.TOOL_H + 4

        y += 6
        # Fill toggle
        self._fill_rect = pygame.Rect(x, y, w, 26)
        y += 32

        # Radius display
        self._radius_rect = pygame.Rect(x, y, w, self.RADIUS_H)
        y += self.RADIUS_H + 10

        # Palette swatches (3 columns)
        cols = 3
        sz   = self.SWATCH_SZ
        gap  = self.SWATCH_GAP
        for i, color in enumerate(PALETTE):
            col = i % cols
            row = i // cols
            sx  = x + col * (sz + gap)
            sy  = y + row * (sz + gap)
            self._swatch_rects.append((pygame.Rect(sx, sy, sz, sz), color))

    def hit_tool(self, pos) -> str | None:
        for name, rect in self._tool_rects.items():
            if rect.collidepoint(pos):
                return name
        return None

    def hit_fill_toggle(self, pos) -> bool:
        return self._fill_rect.collidepoint(pos)

    def hit_swatch(self, pos) -> tuple | None:
        for rect, color in self._swatch_rects:
            if rect.collidepoint(pos):
                return color
        return None

    def draw(self, surf, active_tool, active_color, radius, filled, mouse_pos):
        # Background
        pygame.draw.rect(surf, C_TOOLBAR_BG, (self.x, 0, self.w, self.h))
        pygame.draw.line(surf, C_TOOLBAR_EDGE, (self.x, 0), (self.x, self.h), 2)

        p = self.PAD
        x = self.x + p

        # Title
        title = self.font_med.render("PAINT", True, C_TOOL_ACTIVE)
        surf.blit(title, (self.x + (self.w - title.get_width()) // 2, p + 2))

        # Tool buttons
        for name, rect in self._tool_rects.items():
            is_active = (name == active_tool)
            is_hover  = rect.collidepoint(mouse_pos) and not is_active
            bg = C_TOOL_ACTIVE if is_active else (C_TOOL_HOVER if is_hover else C_TOOL_NORMAL)
            draw_rounded_rect(surf, bg, rect, radius=6)
            draw_rounded_rect(surf, C_TOOL_BORDER, rect, radius=6, width=1)

            # Draw icon using shapes (no emoji / font issues)
            icon_color = (255, 255, 255) if is_active else C_TEXT
            draw_tool_icon(surf, name, rect.centerx, rect.y + 22, icon_color, size=20)
            lbl = self.font_tiny.render(name, True,
                                        C_TEXT if is_active else C_TEXT_DIM)
            surf.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                             rect.bottom - lbl.get_height() - 4))

        # Fill toggle
        fr = self._fill_rect
        is_fhover = fr.collidepoint(mouse_pos)
        draw_rounded_rect(surf, C_TOOL_HOVER if is_fhover else C_TOOL_NORMAL, fr, 5)
        draw_rounded_rect(surf, C_TOOL_BORDER, fr, 5, width=1)
        fill_label = "FILL ✓" if filled else "FILL ✗"
        fl = self.font_tiny.render(fill_label, True,
                                   C_TOOL_ACTIVE if filled else C_TEXT_DIM)
        surf.blit(fl, (fr.centerx - fl.get_width() // 2,
                       fr.centery - fl.get_height() // 2))

        # Radius display
        rr = self._radius_rect
        draw_rounded_rect(surf, C_TOOL_NORMAL, rr, 5)
        draw_rounded_rect(surf, C_TOOL_BORDER, rr, 5, width=1)
        rl = self.font_tiny.render(f"SIZE: {radius}px", True, C_TEXT_DIM)
        surf.blit(rl, (rr.centerx - rl.get_width() // 2,
                       rr.y + 4))
        # Mini preview circle
        dot_r = min(radius, 12)
        pygame.draw.circle(surf, active_color,
                           (rr.centerx, rr.y + 22), dot_r)

        # Palette swatches
        for rect, color in self._swatch_rects:
            pygame.draw.rect(surf, color, rect)
            if color == active_color:
                pygame.draw.rect(surf, (255, 255, 255), rect, 2)
                pygame.draw.rect(surf, (0, 0, 0), rect, 1)
            else:
                pygame.draw.rect(surf, C_TOOLBAR_BG, rect, 1)

        # Active color big swatch at bottom
        bottom_y = self.h - 44
        big_swatch = pygame.Rect(x, bottom_y, self.w - self.PAD * 2, 28)
        pygame.draw.rect(surf, active_color, big_swatch, border_radius=4)
        pygame.draw.rect(surf, C_TOOL_BORDER, big_swatch, 1, border_radius=4)
        lbl2 = self.font_tiny.render("COLOR", True, C_TEXT_DIM)
        surf.blit(lbl2, (self.x + (self.w - lbl2.get_width()) // 2,
                          bottom_y - 12))


# ───────────────────────────────────────────────────────────────────────────────
# Canvas
# ───────────────────────────────────────────────────────────────────────────────

class Canvas:
    """Manages the drawable surface and undo history."""

    MAX_UNDO = 20

    def __init__(self, w: int, h: int, offset_x: int = 0):
        self.w  = w
        self.h  = h
        self.ox = offset_x
        self.surf = pygame.Surface((w, h))
        self.bg   = checkerboard(w, h)
        self.surf.blit(self.bg, (0, 0))
        self._history: list[pygame.Surface] = []
        self._push_history()

    # ── History ──────────────────────────────────────────────────────────────
    def _push_history(self):
        snap = self.surf.copy()
        self._history.append(snap)
        if len(self._history) > self.MAX_UNDO:
            self._history.pop(0)

    def commit(self):
        """Call after finishing a stroke / shape to save undo snapshot."""
        self._push_history()

    def undo(self):
        if len(self._history) > 1:
            self._history.pop()          # discard current
            self.surf.blit(self._history[-1], (0, 0))

    # ── Coordinate mapping ────────────────────────────────────────────────────
    def to_local(self, screen_pos) -> tuple[int, int]:
        return (screen_pos[0] - self.ox, screen_pos[1])

    def in_bounds(self, local_pos) -> bool:
        return 0 <= local_pos[0] < self.w and 0 <= local_pos[1] < self.h

    # ── Drawing primitives ────────────────────────────────────────────────────
    def draw_pencil(self, p1, p2, color, radius):
        pygame.draw.line(self.surf, color, p1, p2, max(1, radius * 2))
        pygame.draw.circle(self.surf, color, p2, radius)

    def draw_rect(self, p1, p2, color, filled):
        r = rect_from_two_points(p1, p2)
        if r.width < 1 or r.height < 1:
            return
        if filled:
            pygame.draw.rect(self.surf, color, r)
        else:
            pygame.draw.rect(self.surf, color, r, 2)

    def draw_circle(self, p1, p2, color, filled):
        center, radius = circle_from_two_points(p1, p2)
        if radius < 1:
            return
        if filled:
            pygame.draw.circle(self.surf, color, center, radius)
        else:
            pygame.draw.circle(self.surf, color, center, radius, 2)

    def erase(self, p1, p2, radius):
        """Repaint the eraser path with the background tile."""
        # Draw on a temp mask then blit from BG
        er = max(1, radius * 2)
        pygame.draw.line(self.surf, C_CANVAS_BG, p1, p2, er)
        pygame.draw.circle(self.surf, C_CANVAS_BG, p2, radius)
        # Re-stamp BG checkerboard texture under the erased area
        # (keeps the retro aesthetic instead of flat white)
        mask_r = pygame.Rect(min(p1[0], p2[0]) - radius - 2,
                              min(p1[1], p2[1]) - radius - 2,
                              abs(p2[0] - p1[0]) + er + 4,
                              abs(p2[1] - p1[1]) + er + 4)
        mask_r.clamp_ip(self.surf.get_rect())
        self.surf.blit(self.bg, mask_r.topleft, mask_r)

    def clear(self):
        self.surf.blit(self.bg, (0, 0))
        self.commit()

    def blit_to(self, target_surf):
        target_surf.blit(self.surf, (self.ox, 0))

    def pick_color(self, local_pos) -> tuple:
        if self.in_bounds(local_pos):
            return self.surf.get_at(local_pos)[:3]
        return (0, 0, 0)


# ───────────────────────────────────────────────────────────────────────────────
# Preview overlay (for rect / circle drag)
# ───────────────────────────────────────────────────────────────────────────────

class ShapePreview:
    """Draws a ghost shape on screen (above canvas) during drag."""

    def __init__(self):
        self.active    = False
        self.tool      = None
        self.p1        = (0, 0)
        self.p2        = (0, 0)
        self.color     = (0, 0, 0)
        self.filled    = False

    def start(self, tool, p1, color, filled):
        self.active = True
        self.tool   = tool
        self.p1     = p1
        self.p2     = p1
        self.color  = color
        self.filled = filled

    def update(self, p2):
        self.p2 = p2

    def stop(self):
        self.active = False

    def draw(self, surf):
        if not self.active:
            return
        ghost = self.color + (140,)   # semi-transparent

        if self.tool == "RECT":
            r = rect_from_two_points(self.p1, self.p2)
            if r.width < 1 or r.height < 1:
                return
            tmp = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
            if self.filled:
                tmp.fill(ghost)
            else:
                pygame.draw.rect(tmp, ghost, tmp.get_rect(), 2)
            surf.blit(tmp, r.topleft)
            # Corner anchors
            for pt in (self.p1, self.p2,
                        (self.p1[0], self.p2[1]),
                        (self.p2[0], self.p1[1])):
                pygame.draw.circle(surf, (255, 255, 255), pt, 3)
                pygame.draw.circle(surf, self.color, pt, 3, 1)

        elif self.tool == "CIRCLE":
            center, radius = circle_from_two_points(self.p1, self.p2)
            if radius < 1:
                return
            tmp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            cx, cy = radius + 2, radius + 2
            if self.filled:
                pygame.draw.circle(tmp, ghost, (cx, cy), radius)
            else:
                pygame.draw.circle(tmp, ghost, (cx, cy), radius, 2)
            surf.blit(tmp, (center[0] - radius - 2, center[1] - radius - 2))
            # Radius line
            pygame.draw.line(surf, (255, 255, 255), center, self.p2, 1)
            pygame.draw.circle(surf, (255, 255, 255), center, 4)
            pygame.draw.circle(surf, self.color, center, 4, 1)


# ───────────────────────────────────────────────────────────────────────────────
# Cursor helper
# ───────────────────────────────────────────────────────────────────────────────

def draw_cursor(surf, pos, tool, radius, color, on_canvas: bool = True):
    """Custom crosshair cursor — always visible via outline+fill trick."""
    x, y = pos
    clen  = 10
    gap   = 3   # gap around center so it doesn't cover pixel under cursor

    # Double-stroke crosshair: white outline then black fill (visible on any bg)
    for arm in [(-clen, 0, -gap, 0), (gap, 0, clen, 0),
                (0, -clen, 0, -gap), (0, gap, 0, clen)]:
        dx1, dy1, dx2, dy2 = arm
        pygame.draw.line(surf, (255, 255, 255),
                         (x + dx1, y + dy1), (x + dx2, y + dy2), 3)
        pygame.draw.line(surf, (0, 0, 0),
                         (x + dx1, y + dy1), (x + dx2, y + dy2), 1)

    if on_canvas and tool == "PENCIL":
        pygame.draw.circle(surf, (255, 255, 255), (x, y), radius + 1, 2)
        pygame.draw.circle(surf, color,            (x, y), radius + 1, 1)
    elif on_canvas and tool == "ERASER":
        pygame.draw.circle(surf, (255, 255, 255), (x, y), radius + 1, 2)
        pygame.draw.circle(surf, (180, 180, 180), (x, y), radius + 1, 1)
    elif not on_canvas:
        # On toolbar: show a small pointer arrow tip
        pygame.draw.circle(surf, (255, 255, 255), (x, y), 3, 2)
        pygame.draw.circle(surf, (0, 0, 0),        (x, y), 3, 1)


# ───────────────────────────────────────────────────────────────────────────────
# Status bar
# ───────────────────────────────────────────────────────────────────────────────

def draw_status(surf, font, tool, color, radius, filled, mouse_pos, canvas_offset):
    bar_h = 20
    bar_y = WINDOW_H - bar_h
    pygame.draw.rect(surf, C_TOOLBAR_BG, (canvas_offset, bar_y, CANVAS_W, bar_h))
    pygame.draw.line(surf, C_TOOLBAR_EDGE, (canvas_offset, bar_y), (WINDOW_W, bar_y))

    cx, cy = mouse_pos[0] - canvas_offset, mouse_pos[1]
    parts = [
        f"Tool: {tool}",
        f"Size: {radius}px",
        f"Pos: ({max(0, cx)}, {max(0, cy)})",
    ]
    if tool in ("RECT", "CIRCLE"):
        parts.append("FILLED" if filled else "OUTLINE")
    parts.append("[1-4] tools  [F] fill  [[ ]] size  [C] clear  [Z] undo  [S] save")

    text = "  |  ".join(parts)
    ts   = font.render(text, True, C_TEXT_DIM)
    surf.blit(ts, (canvas_offset + 8, bar_y + 3))


# ───────────────────────────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    pygame.display.set_caption("Paint Extended — pixel retro edition")
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock  = pygame.time.Clock()
    pygame.mouse.set_visible(False)   # use custom cursor

    font_status = load_font(11)

    toolbar = Toolbar(x=0, total_h=WINDOW_H)
    canvas  = Canvas(w=CANVAS_W, h=CANVAS_H - 20, offset_x=TOOLBAR_W)
    preview = ShapePreview()

    # State
    active_tool  = "PENCIL"
    active_color = PALETTE[0]     # black
    radius       = 6
    filled       = True
    drawing      = False
    last_pos     = None           # for pencil continuity

    def canvas_pos(screen_p):
        return canvas.to_local(screen_p)

    def commit_shape():
        """Write the currently previewed shape permanently to canvas."""
        p1l = canvas_pos(preview.p1)
        p2l = canvas_pos(preview.p2)
        if active_tool == "RECT":
            canvas.draw_rect(p1l, p2l, active_color, filled)
        elif active_tool == "CIRCLE":
            canvas.draw_circle(p1l, p2l, active_color, filled)
        canvas.commit()

    # ── Loop ────────────────────────────────────────────────────────────────
    while True:
        mouse_pos   = pygame.mouse.get_pos()
        mouse_local = canvas_pos(mouse_pos)
        on_canvas   = mouse_pos[0] >= TOOLBAR_W

        pressed   = pygame.key.get_pressed()
        ctrl_held = pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]
        alt_held  = pressed[pygame.K_LALT]  or pressed[pygame.K_RALT]

        for event in pygame.event.get():
            # ── Quit ──────────────────────────────────────────────────────
            if event.type == pygame.QUIT:
                pygame.quit(); return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); return
                if event.key == pygame.K_w and ctrl_held:
                    pygame.quit(); return
                if event.key == pygame.K_F4 and alt_held:
                    pygame.quit(); return

                # Tool select
                if event.key in TOOL_KEYS:
                    active_tool = TOOL_KEYS[event.key]

                # Fill toggle
                elif event.key == pygame.K_f:
                    filled = not filled

                # Radius
                elif event.key == pygame.K_LEFTBRACKET:
                    radius = max(1, radius - 1)
                elif event.key == pygame.K_RIGHTBRACKET:
                    radius = min(60, radius + 1)

                # Clear
                elif event.key == pygame.K_c:
                    canvas.clear()

                # Undo
                elif event.key == pygame.K_z and ctrl_held:
                    canvas.undo()

                # Save
                elif event.key == pygame.K_s:
                    save_path = os.path.join(os.path.dirname(__file__), "paint_save.png")
                    pygame.image.save(canvas.surf, save_path)
                    print(f"[saved] {save_path}")

            # ── Mouse button ──────────────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Right click always shrinks radius (from Part 6)
                if event.button == 3:
                    radius = max(1, radius - 1)
                    continue

                if event.button != 1:
                    continue

                # Toolbar clicks
                if not on_canvas:
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

                # Canvas click — start drawing
                drawing = True
                lp = mouse_local

                if active_tool == "PENCIL":
                    last_pos = lp
                    if canvas.in_bounds(lp):
                        pygame.draw.circle(canvas.surf, active_color, lp, radius)

                elif active_tool == "ERASER":
                    last_pos = lp
                    if canvas.in_bounds(lp):
                        canvas.erase(lp, lp, radius)

                elif active_tool in ("RECT", "CIRCLE"):
                    preview.start(active_tool, mouse_pos, active_color, filled)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and drawing:
                    drawing = False
                    if active_tool in ("RECT", "CIRCLE") and preview.active:
                        commit_shape()
                        preview.stop()
                    elif active_tool in ("PENCIL", "ERASER"):
                        canvas.commit()
                    last_pos = None

            # ── Mouse motion ──────────────────────────────────────────────
            if event.type == pygame.MOUSEMOTION and drawing:
                lp = mouse_local

                if active_tool == "PENCIL" and last_pos is not None:
                    if canvas.in_bounds(lp):
                        canvas.draw_pencil(last_pos, lp, active_color, radius)
                    last_pos = lp

                elif active_tool == "ERASER" and last_pos is not None:
                    if canvas.in_bounds(lp):
                        canvas.erase(last_pos, lp, radius)
                    last_pos = lp

                elif active_tool in ("RECT", "CIRCLE") and preview.active:
                    preview.update(mouse_pos)

        # ── Render ──────────────────────────────────────────────────────────
        # Draw canvas
        canvas.blit_to(screen)

        # Shape preview overlay (above canvas)
        if preview.active:
            preview.draw(screen)

        # Toolbar
        toolbar.draw(screen, active_tool, active_color, radius, filled, mouse_pos)

        # Status bar
        draw_status(screen, font_status, active_tool, active_color,
                    radius, filled, mouse_pos, TOOLBAR_W)

        # Custom cursor always drawn — visible on canvas AND toolbar
        draw_cursor(screen, mouse_pos, active_tool, radius, active_color, on_canvas)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
