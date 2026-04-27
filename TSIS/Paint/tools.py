"""
tools.py — Drawing helpers for Paint Extended (TSIS 2)
"""

import math
import pygame
from collections import deque


# ── Flood Fill ────────────────────────────────────────────────────────────────

def flood_fill(surface: pygame.Surface, start_pos: tuple, fill_color: tuple) -> None:
    """BFS flood fill using PixelArray for speed."""
    sx, sy = int(start_pos[0]), int(start_pos[1])
    w, h = surface.get_size()
    if not (0 <= sx < w and 0 <= sy < h):
        return

    fc = fill_color[:3]

    pa = pygame.PixelArray(surface)
    target_mapped = pa[sx][sy]
    fill_mapped   = surface.map_rgb(*fc)

    if target_mapped == fill_mapped:
        del pa
        return

    queue = deque([(sx, sy)])
    pa[sx][sy] = fill_mapped

    while queue:
        cx, cy = queue.popleft()
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and pa[nx][ny] == target_mapped:
                pa[nx][ny] = fill_mapped
                queue.append((nx, ny))

    del pa


# ── Shape helpers ─────────────────────────────────────────────────────────────

def rect_from_two_points(p1, p2) -> pygame.Rect:
    x = min(p1[0], p2[0])
    y = min(p1[1], p2[1])
    return pygame.Rect(x, y, abs(p2[0] - p1[0]), abs(p2[1] - p1[1]))


def square_from_two_points(p1, p2) -> pygame.Rect:
    """Force equal width/height (min of the two deltas)."""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    side = min(abs(dx), abs(dy))
    sx = p1[0] + (side if dx >= 0 else -side)
    sy = p1[1] + (side if dy >= 0 else -side)
    x  = min(p1[0], sx)
    y  = min(p1[1], sy)
    return pygame.Rect(x, y, side, side)


def right_triangle_points(p1, p2) -> list:
    """Right angle at p1, horizontal and vertical legs."""
    return [p1, (p2[0], p1[1]), (p2[0], p2[1])]


def equilateral_triangle_points(p1, p2) -> list:
    """Equilateral triangle with base from p1 to p2."""
    bx = (p1[0] + p2[0]) / 2
    base_len = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    h = base_len * (math.sqrt(3) / 2)
    # apex above midpoint
    apex = (bx, (p1[1] + p2[1]) / 2 - h / 2)
    return [p1, p2, apex]


def rhombus_points(p1, p2) -> list:
    """Rhombus from bounding box p1→p2; vertices at midpoints of edges."""
    cx = (p1[0] + p2[0]) / 2
    cy = (p1[1] + p2[1]) / 2
    return [
        (cx,     p1[1]),   # top
        (p2[0],  cy),      # right
        (cx,     p2[1]),   # bottom
        (p1[0],  cy),      # left
    ]


def circle_from_two_points(p1, p2) -> tuple:
    """Returns (center, radius)."""
    r = int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]))
    return p1, r


# ── Draw on surface ───────────────────────────────────────────────────────────

def draw_shape(surf: pygame.Surface, tool: str, p1, p2,
               color: tuple, filled: bool, width: int = 2) -> None:
    """Draw a committed shape onto *surf* (local coordinates)."""
    lw = 0 if filled else max(1, width)

    if tool == "RECT":
        r = rect_from_two_points(p1, p2)
        if r.width > 0 and r.height > 0:
            pygame.draw.rect(surf, color, r, lw)

    elif tool == "SQUARE":
        r = square_from_two_points(p1, p2)
        if r.width > 0:
            pygame.draw.rect(surf, color, r, lw)

    elif tool == "CIRCLE":
        center, radius = circle_from_two_points(p1, p2)
        if radius > 0:
            pygame.draw.circle(surf, color, center, radius, lw)

    elif tool == "RTRI":
        pts = right_triangle_points(p1, p2)
        pygame.draw.polygon(surf, color, pts, lw)

    elif tool == "EQTRI":
        pts = equilateral_triangle_points(p1, p2)
        pygame.draw.polygon(surf, color, [(int(x), int(y)) for x, y in pts], lw)

    elif tool == "RHOMBUS":
        pts = rhombus_points(p1, p2)
        pygame.draw.polygon(surf, color, [(int(x), int(y)) for x, y in pts], lw)

    elif tool == "LINE":
        pygame.draw.line(surf, color, p1, p2, max(1, width))
