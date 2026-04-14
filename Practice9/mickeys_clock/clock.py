"""
clock.py — Mickey's Clock core logic
Pixel-art style, 1:1 pixel rendering.
"""

import math
import datetime
import pygame


# ── Palette ────────────────────────────────────────────────────────────────
BLACK       = (  0,   0,   0)
WHITE       = (255, 255, 255)
YELLOW      = (255, 220,   0)
RED         = (200,  30,  30)
DARK_GRAY   = ( 30,  30,  30)
LIGHT_GRAY  = (180, 180, 180)
MICKEY_SKIN = (255, 200, 100)
MICKEY_DARK = ( 20,  20,  20)   # Mickey's black body / ears
CLOCK_BG    = ( 15,  10,  25)   # Deep midnight blue
FACE_COLOR  = (245, 240, 220)   # Creamy clock face
TICK_COLOR  = ( 60,  40,  80)
HAND_MINUTE = (200,  50,  50)   # Red = minute (right hand)
HAND_SECOND = ( 50, 180, 230)   # Cyan = second (left hand)
SHADOW      = (  0,   0,   0, 100)


def draw_pixel_circle(surf, color, cx, cy, r, width=0):
    """Draw a circle using pixel-perfect integer math."""
    pygame.draw.circle(surf, color, (cx, cy), r, width)


def draw_pixel_rect(surf, color, rect):
    pygame.draw.rect(surf, color, rect)


class MickeyClock:
    """
    Renders a pixel-art Mickey Mouse clock.
    Mickey's RIGHT hand → minutes  (red)
    Mickey's LEFT  hand → seconds  (cyan)
    """

    SCALE = 3          # Each "pixel" is SCALE × SCALE screen pixels
    CLOCK_R = 60       # Clock face radius in logical pixels
    BODY_R  = 28       # Mickey body radius
    EAR_R   = 16       # Ear radius
    HEAD_R  = 22       # Head radius

    def __init__(self, surface: pygame.Surface):
        self.surf = surface
        self.w, self.h = surface.get_size()
        self.cx = self.w // 2
        self.cy = self.h // 2

        # Pixel-perfect canvas (1:1 logical pixels)
        self.canvas = pygame.Surface(
            (self.w // self.SCALE, self.h // self.SCALE)
        )
        self.lw = self.canvas.get_width()
        self.lh = self.canvas.get_height()
        self.lcx = self.lw // 2
        self.lcy = self.lh // 2

        self._load_hands()
        self._build_face_cache()

    # ── Asset loading ───────────────────────────────────────────────────────

    def _load_hands(self):
        """Load or generate Mickey hand sprites."""
        import os
        right_path = os.path.join(
            os.path.dirname(__file__), "images", "mickey_hand_right.png"
        )
        left_path = os.path.join(
            os.path.dirname(__file__), "images", "mickey_hand_left.png"
        )

        try:
            self.hand_right_src = pygame.image.load(right_path).convert_alpha()
            self.hand_left_src  = pygame.image.load(left_path).convert_alpha()
        except FileNotFoundError:
            # Fallback: generate procedurally
            self.hand_right_src = self._make_hand_surface(HAND_MINUTE)
            self.hand_left_src  = self._make_hand_surface(HAND_SECOND)

    def _make_hand_surface(self, color):
        """Procedural pixel-art glove hand (16 × 40 logical px)."""
        W, H = 16, 40
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))

        C  = (*color, 255)
        OL = (20, 20, 20, 255)

        # Fingertip bulge
        pygame.draw.circle(s, C, (W//2, 5), 5)
        # Palm
        pygame.draw.rect(s, C, (3, 5, 10, 18))
        # Knuckle line
        pygame.draw.line(s, OL, (4, 10), (11, 10), 1)
        # Thumb bump (right side for right-hand feel)
        pygame.draw.circle(s, C, (13, 13), 3)
        # Wrist
        pygame.draw.rect(s, C, (4, 23, 8, 10))
        # Cuff stripe
        pygame.draw.rect(s, OL, (4, 22, 8, 2))

        # Outline pass
        pixel_set = set()
        for x in range(W):
            for y in range(H):
                if s.get_at((x, y))[3] > 0:
                    pixel_set.add((x, y))
        for (x, y) in list(pixel_set):
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x+dx, y+dy
                if (nx, ny) not in pixel_set and 0 <= nx < W and 0 <= ny < H:
                    cur = s.get_at((nx, ny))
                    if cur[3] == 0:
                        s.set_at((nx, ny), OL)

        return s

    # ── Static face cache ───────────────────────────────────────────────────

    def _build_face_cache(self):
        """Pre-render static parts of the clock face."""
        c = self.canvas
        W, H = self.lw, self.lh
        cx, cy = self.lcx, self.lcy
        R = self.CLOCK_R

        self._face_cache = pygame.Surface((W, H))
        fc = self._face_cache
        fc.fill(CLOCK_BG)

        # ── Decorative background pattern ──────────────────────────────────
        # Pixel grid dots
        for x in range(0, W, 4):
            for y in range(0, H, 4):
                fc.set_at((x, y), (25, 18, 40))

        # ── Clock shadow ───────────────────────────────────────────────────
        pygame.draw.circle(fc, (5, 5, 15), (cx + 2, cy + 3), R + 6)

        # ── Outer bezel (pixel-thick rings) ───────────────────────────────
        pygame.draw.circle(fc, DARK_GRAY,  (cx, cy), R + 7)
        pygame.draw.circle(fc, YELLOW,     (cx, cy), R + 5)
        pygame.draw.circle(fc, DARK_GRAY,  (cx, cy), R + 3)

        # ── Clock face ─────────────────────────────────────────────────────
        pygame.draw.circle(fc, FACE_COLOR, (cx, cy), R)

        # ── Hour tick marks ────────────────────────────────────────────────
        for h in range(12):
            angle = math.radians(h * 30 - 90)
            inner = R - 8 if h % 3 == 0 else R - 5
            outer = R - 2
            x1 = cx + int(inner * math.cos(angle))
            y1 = cy + int(inner * math.sin(angle))
            x2 = cx + int(outer * math.cos(angle))
            y2 = cy + int(outer * math.sin(angle))
            w  = 2 if h % 3 == 0 else 1
            pygame.draw.line(fc, DARK_GRAY, (x1, y1), (x2, y2), w)

        # ── Minute tick marks ──────────────────────────────────────────────
        for m in range(60):
            if m % 5 == 0:
                continue
            angle = math.radians(m * 6 - 90)
            x1 = cx + int((R - 3) * math.cos(angle))
            y1 = cy + int((R - 3) * math.sin(angle))
            x2 = cx + int((R - 1) * math.cos(angle))
            y2 = cy + int((R - 1) * math.sin(angle))
            fc.set_at((x1, y1), LIGHT_GRAY)

        # ── Mickey body (below the face layer, decorative) ─────────────────
        # We'll draw Mickey's iconic silhouette centered under the clock
        body_y = cy + R + 14
        body_r = self.BODY_R

        # Body
        pygame.draw.circle(fc, MICKEY_DARK, (cx, body_y), body_r)
        # Ear left
        pygame.draw.circle(fc, MICKEY_DARK, (cx - 20, body_y - 22), self.EAR_R)
        # Ear right
        pygame.draw.circle(fc, MICKEY_DARK, (cx + 20, body_y - 22), self.EAR_R)
        # Head
        pygame.draw.circle(fc, MICKEY_DARK, (cx, body_y - 15), self.HEAD_R)
        # Face highlight
        pygame.draw.circle(fc, (40, 40, 40), (cx, body_y - 14), self.HEAD_R - 2)
        # Eyes
        pygame.draw.circle(fc, WHITE, (cx - 7, body_y - 20), 4)
        pygame.draw.circle(fc, WHITE, (cx + 7, body_y - 20), 4)
        pygame.draw.circle(fc, BLACK, (cx - 6, body_y - 19), 2)
        pygame.draw.circle(fc, BLACK, (cx + 6, body_y - 19), 2)
        # Nose
        pygame.draw.ellipse(fc, BLACK, (cx - 5, body_y - 14, 10, 6))
        # Smile
        pygame.draw.arc(fc, BLACK,
                        (cx - 8, body_y - 12, 16, 8),
                        math.pi + 0.3, math.pi * 2 - 0.3, 1)

        # Shorts (two legs)
        pygame.draw.rect(fc, RED, (cx - body_r + 4, body_y + 10, body_r * 2 - 8, 8))
        for leg_x in [cx - 10, cx + 2]:
            pygame.draw.rect(fc, MICKEY_DARK, (leg_x, body_y + 14, 8, 12))

        # Buttons on shorts
        for bx in [cx - 4, cx + 4]:
            pygame.draw.circle(fc, YELLOW, (bx, body_y + 14), 2)

    # ── Hand rendering ──────────────────────────────────────────────────────

    def _draw_hand(self, canvas, hand_src, angle_deg, length, color, pivot_offset=0):
        """
        Draw a rotated Mickey hand.
        angle_deg: 0 = pointing up (12 o'clock), clockwise positive.
        pivot_offset: how many px from tip to the pivot point.
        """
        cx, cy = self.lcx, self.lcy

        # Rotate sprite: pygame rotates counter-clockwise, so negate
        rotated = pygame.transform.rotate(hand_src, -angle_deg)
        rw, rh = rotated.get_size()

        # Compute where to place the rotated surface so its "bottom" 
        # (wrist end) is at the clock center.
        rad = math.radians(angle_deg - 90)
        # Offset from center toward tip direction
        tip_x = cx + int(length * math.cos(rad))
        tip_y = cy + int(length * math.sin(rad))

        # Blit centered on the midpoint between center and tip
        mid_x = (cx + tip_x) // 2
        mid_y = (cy + tip_y) // 2
        blit_x = mid_x - rw // 2
        blit_y = mid_y - rh // 2

        canvas.blit(rotated, (blit_x, blit_y))

        # Center dot
        pygame.draw.circle(canvas, color, (cx, cy), 3)
        pygame.draw.circle(canvas, DARK_GRAY, (cx, cy), 3, 1)

    def _draw_hand_line(self, canvas, angle_deg, length, color, width=2):
        """Pixel-art line hand as fallback / underlay."""
        cx, cy = self.lcx, self.lcy
        rad = math.radians(angle_deg - 90)
        ex = cx + int(length * math.cos(rad))
        ey = cy + int(length * math.sin(rad))
        # Counter-balance tail
        tx = cx - int(8 * math.cos(rad))
        ty = cy - int(8 * math.sin(rad))
        pygame.draw.line(canvas, DARK_GRAY, (tx, ty), (ex, ey), width + 1)
        pygame.draw.line(canvas, color,     (tx, ty), (ex, ey), width)

    # ── Main render ─────────────────────────────────────────────────────────

    def render(self, now: datetime.datetime):
        """Draw the complete clock for the given datetime onto self.surf."""
        canvas = self.canvas
        canvas.blit(self._face_cache, (0, 0))

        minutes = now.minute
        seconds = now.second

        # Angles: 0° = 12-o'clock (up), clockwise
        # Minutes: full rotation in 60 min
        min_angle = minutes * 6 + seconds * 0.1   # smooth minute hand
        # Seconds: full rotation in 60 sec
        sec_angle = seconds * 6

        R = self.CLOCK_R
        min_len = int(R * 0.70)
        sec_len = int(R * 0.80)

        # Underlay line hands for crisp pixel look
        self._draw_hand_line(canvas, min_angle, min_len, HAND_MINUTE, 2)
        self._draw_hand_line(canvas, sec_angle, sec_len, HAND_SECOND, 1)

        # Mickey glove hands on top
        self._draw_hand(canvas, self.hand_right_src, min_angle, min_len, HAND_MINUTE)
        self._draw_hand(canvas, self.hand_left_src,  sec_angle, sec_len, HAND_SECOND)

        # Center cap
        cx, cy = self.lcx, self.lcy
        pygame.draw.circle(canvas, YELLOW,     (cx, cy), 4)
        pygame.draw.circle(canvas, DARK_GRAY,  (cx, cy), 4, 1)

        # ── Digital time readout (pixel font style) ─────────────────────
        font = pygame.font.SysFont("monospace", 8, bold=True)
        time_str = f"{minutes:02d}:{seconds:02d}"
        txt = font.render(time_str, False, DARK_GRAY)
        tw, th = txt.get_size()
        canvas.blit(txt, (cx - tw // 2, cy + R - 24))

        # Legend labels
        small = pygame.font.SysFont("monospace", 6)
        m_lbl = small.render("MIN", False, HAND_MINUTE)
        s_lbl = small.render("SEC", False, HAND_SECOND)
        canvas.blit(m_lbl, (5, 5))
        canvas.blit(s_lbl, (self.lw - 20, 5))

        # ── Scale canvas → display surface (nearest-neighbor = pixel art) ──
        scaled = pygame.transform.scale(
            canvas,
            (self.lw * self.SCALE, self.lh * self.SCALE)
        )
        # Center on screen
        ox = (self.w - scaled.get_width())  // 2
        oy = (self.h - scaled.get_height()) // 2
        self.surf.fill(CLOCK_BG)
        self.surf.blit(scaled, (ox, oy))
