"""
renderer.py
===========
All Pygame drawing logic for the Snake game.
The Renderer class reads game-state objects and blits them to the screen.
Keeping rendering separate from logic makes both easier to test and extend.

New in Practice 8 extension
----------------------------
  • _draw_food_item()   : draws one FoodItem using its FoodConfig colours.
  • _draw_timer_ring()  : draws a shrinking arc around food showing time left.
  • _draw_food_items()  : iterates over all active items in a FoodManager.
  • draw_frame() now accepts a FoodManager instead of a single Food.
  • Weight label drawn on rarer food items (Cherry / Golden).
"""

import math
import pygame
import settings as S
from snake import Snake, FoodItem, FoodManager, LevelSystem


class Renderer:
    """
    Draws the complete game frame each tick.

    Public methods
    --------------
    draw_frame()     — one full frame (HUD + walls + grid + food + snake)
    draw_game_over() — semi-transparent game-over overlay
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen

        # ── Fonts (monospace for the retro terminal look) ──────────────────
        try:
            self._font_big   = pygame.font.SysFont("monospace", 22, bold=True)
            self._font_med   = pygame.font.SysFont("monospace", 16, bold=True)
            self._font_small = pygame.font.SysFont("monospace", 13, bold=True)
            self._font_tiny  = pygame.font.SysFont("monospace", 10, bold=True)
            self._font_huge  = pygame.font.SysFont("monospace", 52, bold=True)
        except Exception:
            # Fallback when the system has no monospace font installed
            self._font_big   = pygame.font.Font(None, 26)
            self._font_med   = pygame.font.Font(None, 20)
            self._font_small = pygame.font.Font(None, 16)
            self._font_tiny  = pygame.font.Font(None, 13)
            self._font_huge  = pygame.font.Font(None, 60)

        # Pre-build static surfaces that never change between frames.
        # Drawing them once and reusing is much faster than redrawing every tick.
        self._wall_surf = self._build_wall_surface()
        self._grid_surf = self._build_grid_surface()

    # ════════════════════════════════════════════════════════════════════════
    #  Static surface builders  (called once during __init__)
    # ════════════════════════════════════════════════════════════════════════

    def _build_wall_surface(self) -> pygame.Surface:
        """
        Draw all border-wall cells onto a transparent surface.
        Each wall cell gets:
          • A solid fill in COL_WALL
          • A 1-px top+left highlight for a bevelled retro look
          • A dark bottom-right pixel as a drop-shadow
        """
        surf = pygame.Surface((S.WIN_W, S.WIN_H), pygame.SRCALPHA)
        C = S.CELL

        for col in range(S.COLS):
            for row in range(S.ROWS):
                # A cell belongs to the wall if it lies outside the play area
                is_wall = (col < S.WALL_THICKNESS or
                           col >= S.COLS - S.WALL_THICKNESS or
                           row < S.WALL_THICKNESS or
                           row >= S.ROWS - S.WALL_THICKNESS)
                if is_wall:
                    x, y = col * C, row * C
                    pygame.draw.rect(surf, S.COL_WALL, (x, y, C, C))
                    # Top-edge highlight (lighter)
                    pygame.draw.line(surf, S.COL_WALL_HL, (x, y), (x + C - 2, y))
                    # Left-edge highlight (lighter)
                    pygame.draw.line(surf, S.COL_WALL_HL, (x, y), (x, y + C - 2))
                    # Bottom-right shadow pixel (darker)
                    pygame.draw.rect(surf, (10, 30, 10), (x + C - 2, y + C - 2, 2, 2))
        return surf

    def _build_grid_surface(self) -> pygame.Surface:
        """
        Draw faint gridlines over the play area onto a transparent surface.
        These help players count cells when navigating.
        """
        surf = pygame.Surface((S.WIN_W, S.WIN_H), pygame.SRCALPHA)
        C = S.CELL

        # Vertical lines (one per column boundary inside play area)
        for col in range(S.PLAY_LEFT, S.PLAY_RIGHT + 2):
            x = col * C
            pygame.draw.line(surf, (*S.COL_GRID, 255),
                             (x, S.PLAY_TOP * C),
                             (x, (S.PLAY_BOTTOM + 1) * C))

        # Horizontal lines (one per row boundary inside play area)
        for row in range(S.PLAY_TOP, S.PLAY_BOTTOM + 2):
            y = row * C
            pygame.draw.line(surf, (*S.COL_GRID, 255),
                             (S.PLAY_LEFT * C, y),
                             ((S.PLAY_RIGHT + 1) * C, y))
        return surf

    # ════════════════════════════════════════════════════════════════════════
    #  Per-cell drawing helpers
    # ════════════════════════════════════════════════════════════════════════

    def _cell_rect(self, col: int, row: int) -> pygame.Rect:
        """Return the screen-pixel Rect for grid cell (col, row)."""
        return pygame.Rect(col * S.CELL, row * S.CELL, S.CELL, S.CELL)

    # ── Snake ────────────────────────────────────────────────────────────────

    def _draw_snake_segment(self, col: int, row: int,
                            is_head: bool, direction: tuple,
                            index: int) -> None:
        """
        Draw one snake segment with pixel-art styling.

        The head gets eyes facing the movement direction.
        Body segments gradually darken toward the tail using linear
        interpolation between COL_SNAKE_BODY and COL_SNAKE_DARK.
        """
        C   = S.CELL
        x   = col * C
        y   = row * C
        pad = 2   # inner padding so there are visible gaps between segments

        # ── Segment colour ─────────────────────────────────────────────────
        if is_head:
            colour = S.COL_SNAKE_HEAD
        else:
            # Linearly interpolate toward a darker shade; max effect at seg 12
            t = min(index / 12, 1.0)
            r = int(S.COL_SNAKE_BODY[0] * (1 - t) + S.COL_SNAKE_DARK[0] * t)
            g = int(S.COL_SNAKE_BODY[1] * (1 - t) + S.COL_SNAKE_DARK[1] * t)
            b = int(S.COL_SNAKE_BODY[2] * (1 - t) + S.COL_SNAKE_DARK[2] * t)
            colour = (r, g, b)

        # ── Body fill ──────────────────────────────────────────────────────
        pygame.draw.rect(self.screen, colour,
                         (x + pad, y + pad, C - pad * 2, C - pad * 2),
                         border_radius=3)

        # ── Top-left highlight stripe ──────────────────────────────────────
        hl = (min(colour[0] + 50, 255),
              min(colour[1] + 70, 255),
              min(colour[2] + 30, 255))
        pygame.draw.rect(self.screen, hl,
                         (x + pad, y + pad, C - pad * 2 - 2, 2))

        # ── Eyes on the head ───────────────────────────────────────────────
        if is_head:
            self._draw_eyes(x, y, direction)

    def _draw_eyes(self, x: int, y: int, direction: tuple) -> None:
        """
        Draw two small pupil dots on the head cell offset in the facing direction.
        The two eyes are spread perpendicular to movement using a cross product.
        """
        C  = S.CELL
        dx, dy = direction
        cx = x + C // 2
        cy = y + C // 2

        # Offset toward the facing edge
        ox = dx * (C // 4)
        oy = dy * (C // 4)

        # Perpendicular offset for the two eye positions (intentional dx/dy swap)
        px = dy * (C // 5)
        py = dx * (C // 5)

        eye_r = 2
        for sign in (-1, 1):
            ex = cx + ox + sign * px
            ey = cy + oy + sign * py
            pygame.draw.circle(self.screen, S.COL_SNAKE_EYE, (ex, ey), eye_r)
            pygame.draw.circle(self.screen, (0, 0, 0), (ex, ey), 1)  # pupil

    # ── Food ─────────────────────────────────────────────────────────────────

    def _draw_timer_ring(self, cx: int, cy: int, radius: int,
                         fraction: float, color: tuple) -> None:
        """
        Draw a partial arc around a food item showing how much time remains.

        The arc starts at the top (12 o'clock) and sweeps clockwise.
        A full arc (fraction=1.0) = just spawned.
        A tiny arc (fraction≈0.0) = about to expire.

        Parameters
        ----------
        cx, cy   : pixel centre of the food cell
        radius   : arc radius in pixels (slightly larger than the food sprite)
        fraction : remaining lifetime as 0.0–1.0
        color    : arc colour (taken from FoodConfig.col_timer)
        """
        if fraction <= 0:
            return   # nothing to draw

        # Rect that bounds the arc circle
        # pygame.draw.arc uses math angles: 0=right, π/2=up (because Y is flipped,
        # π/2 appears at the top on screen).
        arc_rect = pygame.Rect(cx - radius, cy - radius,
                               radius * 2, radius * 2)

        # We want to start at the top (12 o'clock) = π/2 in pygame math coords.
        # The arc sweeps counter-clockwise in pygame convention, but because the
        # Y axis is flipped on screen it appears clockwise — which is intuitive
        # for a countdown (ticks away to the right like a clock).
        start_angle = math.pi / 2                       # top of circle
        end_angle   = start_angle + fraction * 2 * math.pi  # sweep clockwise on screen

        # pygame.draw.arc needs start < stop in standard math direction;
        # we clamp end_angle to avoid floating-point overshoot
        end_angle = min(end_angle, start_angle + 2 * math.pi - 0.001)

        try:
            pygame.draw.arc(self.screen, color, arc_rect,
                            start_angle, end_angle, 2)
        except Exception:
            pass   # very small arcs occasionally raise in some pygame builds

    def _draw_food_item(self, item: FoodItem) -> None:
        """
        Draw one food item as a pixel-art sprite with a timer arc around it.

        Sprite style varies by food type via FoodConfig colours.
        The item blinks (skips every other render) when below the blink
        threshold (FOOD_BLINK_THRESHOLD fraction of lifetime remaining).

        Visual layers (bottom → top):
          1. Timer arc ring   — shows remaining lifetime
          2. Apple-style body — circular fill + highlight spot
          3. Stem + leaf
          4. Weight label     — shown for non-APPLE types (×3, ×8 …)
        """
        if item.pos is None:
            return

        col, row = item.pos
        cfg = item.config   # shorthand for this item's FoodConfig

        # ── Blink effect when near expiry ──────────────────────────────────
        # pygame.time.get_ticks() returns ms since init; alternate every 200ms
        if item.is_blinking and (pygame.time.get_ticks() // 200) % 2 == 0:
            return   # skip this frame — creates the blink

        C  = S.CELL
        x  = col * C
        y  = row * C
        cx = x + C // 2       # pixel centre x
        cy = y + C // 2 + 1   # pixel centre y (shifted down 1px for apple look)
        r  = C // 2 - 3       # sprite radius

        # ── 1. Timer arc ring ──────────────────────────────────────────────
        # Draw the arc just outside the food sprite (radius = sprite_r + 3)
        self._draw_timer_ring(cx, cy - 1, r + 4,
                              item.lifetime_fraction, cfg.col_timer)

        # ── 2. Body fill ───────────────────────────────────────────────────
        pygame.draw.circle(self.screen, cfg.col_body, (cx, cy), r)
        # Highlight spot — top-left of the fruit
        pygame.draw.circle(self.screen, cfg.col_highlight,
                           (cx - 2, cy - 2), max(r // 3, 2))

        # ── 3. Stem and leaf ───────────────────────────────────────────────
        # Stem: short diagonal line above the fruit
        pygame.draw.line(self.screen, cfg.col_stem,
                         (cx, cy - r), (cx + 2, cy - r - 4), 2)
        # Leaf: tiny circle next to the stem tip
        pygame.draw.circle(self.screen, cfg.col_stem,
                           (cx + 4, cy - r - 3), 2)

        # ── 4. Weight label for non-APPLE types ───────────────────────────
        # Show "×3" or "×8" so the player knows it's a bonus item
        if cfg.weight > 1:
            label = self._font_tiny.render(f"x{cfg.weight}", True, S.COL_WHITE)
            # Centre the label below the sprite
            lx = cx - label.get_width() // 2
            ly = cy + r + 1
            self.screen.blit(label, (lx, ly))

    def _draw_food_items(self, food_mgr: FoodManager) -> None:
        """
        Draw all active food items from the FoodManager.
        Iterates over food_mgr.items and delegates to _draw_food_item().
        """
        for item in food_mgr.items:
            self._draw_food_item(item)

    # ── HUD ──────────────────────────────────────────────────────────────────

    def _draw_hud(self, level_sys: LevelSystem, food_mgr: FoodManager) -> None:
        """
        Draw the HUD bar below the game grid.

        Shows:
          • Score (left)
          • Food-type legend strip (centre) — coloured dots for active items
          • Level (right, flashing on level-up)
        """
        hud_y = S.WIN_H   # HUD starts directly below the grid
        hud_w = S.WIN_W

        # Background and border
        pygame.draw.rect(self.screen, S.COL_HUD_BG, (0, hud_y, hud_w, S.HUD_H))
        pygame.draw.line(self.screen, S.COL_HUD_BORDER,
                         (0, hud_y), (hud_w, hud_y), 2)

        m = 10   # left/right margin

        # ── Score (left side) ─────────────────────────────────────────────
        label_sc = self._font_small.render("SCORE", True, S.COL_TEXT_DIM)
        value_sc = self._font_big.render(f"{level_sys.score:06d}", True,
                                         S.COL_TEXT_SCORE)
        self.screen.blit(label_sc, (m, hud_y + 4))
        self.screen.blit(value_sc, (m, hud_y + 18))

        # ── Food indicators (centre) ──────────────────────────────────────
        # Show one coloured dot + weight label for each active food item.
        # This helps the player track how many items are on the grid and
        # what their weights are at a glance.
        pip_cx  = hud_w // 2
        pip_y   = hud_y + S.HUD_H // 2
        pip_r   = 5
        pip_gap = 24   # horizontal gap between indicators
        items   = food_mgr.items

        # Centre the row of indicators around pip_cx
        total_w = max(len(items) - 1, 0) * pip_gap
        start_x = pip_cx - total_w // 2

        for i, item in enumerate(items):
            px = start_x + i * pip_gap
            # Dot in the food's body colour
            pygame.draw.circle(self.screen, item.config.col_body, (px, pip_y), pip_r)
            # White outline
            pygame.draw.circle(self.screen, S.COL_WHITE, (px, pip_y), pip_r, 1)
            # Weight label below the dot
            wlbl = self._font_tiny.render(f"x{item.config.weight}", True,
                                          S.COL_TEXT_DIM)
            self.screen.blit(wlbl, (px - wlbl.get_width() // 2, pip_y + pip_r + 2))

        # ── Level (right side) ────────────────────────────────────────────
        # Flash bright yellow immediately after a level-up
        if level_sys.level_up_flash > 0 and level_sys.level_up_flash % 8 < 5:
            lv_colour = S.COL_LEVEL_UP
        else:
            lv_colour = S.COL_TEXT_LEVEL

        label_lv = self._font_small.render("LEVEL", True, S.COL_TEXT_DIM)
        value_lv = self._font_big.render(f"{level_sys.level:02d}", True, lv_colour)
        self.screen.blit(label_lv, (hud_w - 70, hud_y + 4))
        self.screen.blit(value_lv, (hud_w - 70, hud_y + 18))

    # ── Level-up banner ───────────────────────────────────────────────────────

    def _draw_level_up_banner(self, level_sys: LevelSystem) -> None:
        """
        Render a centred "LEVEL UP!" banner while the flash timer is active.
        Uses alpha blending to fade the banner in and out smoothly.
        """
        if level_sys.level_up_flash <= 0:
            return

        # Alpha: ramp from 255 down to 0 during the last quarter of the timer
        alpha = min(255, level_sys.level_up_flash * 10)

        # Main heading
        surf = self._font_huge.render("LEVEL  UP!", True, S.COL_LEVEL_UP)
        surf.set_alpha(alpha)
        self.screen.blit(surf, surf.get_rect(center=(S.WIN_W // 2, S.WIN_H // 2)))

        # Subtitle: current speed after the level-up
        spd = self._font_med.render(f"SPEED  {level_sys.speed:.1f}",
                                    True, S.COL_WHITE)
        spd.set_alpha(alpha)
        self.screen.blit(spd, spd.get_rect(center=(S.WIN_W // 2,
                                                    S.WIN_H // 2 + 52)))

    # ════════════════════════════════════════════════════════════════════════
    #  Public draw methods
    # ════════════════════════════════════════════════════════════════════════

    def draw_frame(self, snake: Snake, food_mgr: FoodManager,
                   level_sys: LevelSystem) -> None:
        """
        Render a complete game frame in layer order:

          1. Background fill
          2. Faint grid overlay
          3. Wall border
          4. All active food items (with timer rings)
          5. Snake body (tail → head so head renders on top)
          6. HUD bar
          7. Level-up banner (if active)
        """
        # 1. Background — fill the entire window with the base colour
        self.screen.fill(S.COL_BG)

        # 2. Faint grid (pre-built transparent surface — cheap blit)
        self.screen.blit(self._grid_surf, (0, 0))

        # 3. Wall border (pre-built transparent surface)
        self.screen.blit(self._wall_surf, (0, 0))

        # 4. All food items — each with its type's colours and a timer ring
        self._draw_food_items(food_mgr)

        # 5. Snake segments — draw tail-to-head so head is always on top
        body = snake.body
        for i in range(len(body) - 1, -1, -1):
            col, row = body[i]
            is_head  = (i == 0)
            self._draw_snake_segment(col, row, is_head, snake.dir, i)

        # 6. HUD bar beneath the grid
        self._draw_hud(level_sys, food_mgr)

        # 7. Level-up banner (fades in/out automatically via its timer)
        self._draw_level_up_banner(level_sys)

    def draw_game_over(self, level_sys: LevelSystem) -> None:
        """
        Draw a semi-transparent dark overlay with the final score and controls.
        Called every frame while game_over is True (after draw_frame).
        """
        # Dark vignette over the entire window
        overlay = pygame.Surface((S.WIN_W, S.WIN_H + S.HUD_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        cx = S.WIN_W // 2
        cy = S.WIN_H // 2

        # "GAME OVER" heading
        go = self._font_huge.render("GAME OVER", True, S.COL_GAMEOVER_TXT)
        self.screen.blit(go, go.get_rect(centerx=cx, centery=cy - 70))

        # Final score
        sc = self._font_big.render(f"SCORE   {level_sys.score:06d}",
                                   True, S.COL_TEXT_SCORE)
        self.screen.blit(sc, sc.get_rect(centerx=cx, centery=cy))

        # Level reached
        lv = self._font_big.render(f"LEVEL   {level_sys.level:02d}",
                                   True, S.COL_TEXT_LEVEL)
        self.screen.blit(lv, lv.get_rect(centerx=cx, centery=cy + 34))

        # Total foods eaten
        fe = self._font_med.render(f"APPLES  {level_sys.foods_eaten}",
                                   True, S.COL_TEXT_DIM)
        self.screen.blit(fe, fe.get_rect(centerx=cx, centery=cy + 66))

        # Restart / quit prompts
        r = self._font_small.render("PRESS  R  TO  RESTART", True, S.COL_WHITE)
        q = self._font_small.render("PRESS  Q  TO  QUIT",    True, (140, 140, 140))
        self.screen.blit(r, r.get_rect(centerx=cx, centery=cy + 108))
        self.screen.blit(q, q.get_rect(centerx=cx, centery=cy + 128))
