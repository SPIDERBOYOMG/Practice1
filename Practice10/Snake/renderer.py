"""
renderer.py
===========
All Pygame drawing logic for the Snake game.
The Renderer class takes game-state objects and blits them onto the screen.
Keeping rendering separate from logic makes both easier to read and test.
"""

import math
import pygame
import settings as S
from snake import Snake, Food, LevelSystem


class Renderer:
    """
    Draws the complete game frame:
      draw_frame()     — one full frame (HUD + walls + grid + food + snake)
      draw_game_over() — semi-transparent game-over overlay
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen

        # ── Fonts (monospace for that retro terminal feel) ─────────────────
        try:
            self._font_big   = pygame.font.SysFont("monospace", 22, bold=True)
            self._font_med   = pygame.font.SysFont("monospace", 16, bold=True)
            self._font_small = pygame.font.SysFont("monospace", 13, bold=True)
            self._font_huge  = pygame.font.SysFont("monospace", 52, bold=True)
        except Exception:
            # Fallback to pygame's built-in font
            self._font_big   = pygame.font.Font(None, 26)
            self._font_med   = pygame.font.Font(None, 20)
            self._font_small = pygame.font.Font(None, 16)
            self._font_huge  = pygame.font.Font(None, 60)

        # Pre-build the static wall surface (drawn once, reused every frame)
        self._wall_surf  = self._build_wall_surface()
        # Pre-build the grid overlay (faint lines over the play area)
        self._grid_surf  = self._build_grid_surface()

    # ── Static surface builders ──────────────────────────────────────────────

    def _build_wall_surface(self) -> pygame.Surface:
        """
        Draw the border wall cells onto a transparent surface.
        Each wall cell gets a block fill + a 1-pixel highlight on
        the top-left edge for a retro bevelled look.
        """
        surf = pygame.Surface((S.WIN_W, S.WIN_H), pygame.SRCALPHA)
        C = S.CELL

        for col in range(S.COLS):
            for row in range(S.ROWS):
                # A cell is a wall if it's outside the inner play area
                is_wall = (
                    col < S.WALL_THICKNESS or
                    col >= S.COLS - S.WALL_THICKNESS or
                    row < S.WALL_THICKNESS or
                    row >= S.ROWS - S.WALL_THICKNESS
                )
                if is_wall:
                    x, y = col * C, row * C
                    # Solid wall block
                    pygame.draw.rect(surf, S.COL_WALL, (x, y, C, C))
                    # 1-px highlight on top edge
                    pygame.draw.line(surf, S.COL_WALL_HL, (x, y), (x + C - 2, y))
                    # 1-px highlight on left edge
                    pygame.draw.line(surf, S.COL_WALL_HL, (x, y), (x, y + C - 2))
                    # Dark bottom-right pixel (shadow)
                    pygame.draw.rect(surf, (10, 30, 10), (x + C - 2, y + C - 2, 2, 2))
        return surf

    def _build_grid_surface(self) -> pygame.Surface:
        """
        Faint grid lines inside the play area so the player can count cells.
        Drawn on a transparent surface so it overlays the background.
        """
        surf = pygame.Surface((S.WIN_W, S.WIN_H), pygame.SRCALPHA)
        C = S.CELL

        # Vertical lines
        for col in range(S.PLAY_LEFT, S.PLAY_RIGHT + 2):
            x = col * C
            pygame.draw.line(surf, (*S.COL_GRID, 255),
                             (x, S.PLAY_TOP * C),
                             (x, (S.PLAY_BOTTOM + 1) * C))
        # Horizontal lines
        for row in range(S.PLAY_TOP, S.PLAY_BOTTOM + 2):
            y = row * C
            pygame.draw.line(surf, (*S.COL_GRID, 255),
                             (S.PLAY_LEFT * C, y),
                             ((S.PLAY_RIGHT + 1) * C, y))
        return surf

    # ── Per-cell drawing helpers ─────────────────────────────────────────────

    def _cell_rect(self, col: int, row: int) -> pygame.Rect:
        """Return the pixel Rect for grid cell (col, row)."""
        return pygame.Rect(col * S.CELL, row * S.CELL, S.CELL, S.CELL)

    def _draw_snake_segment(self, col: int, row: int,
                            is_head: bool, direction: tuple,
                            index: int) -> None:
        """
        Draw one snake segment with pixel-art styling.

        Head gets eyes drawn in the facing direction.
        Body segments get a slight colour gradient (darker toward tail).
        """
        C   = S.CELL
        x   = col * C
        y   = row * C
        pad = 2   # inner padding so segments have visible gaps

        # ── Colour: body darkens slightly toward the tail ──────────────────
        if is_head:
            colour = S.COL_SNAKE_HEAD
        else:
            # Lerp between BODY colour and DARK colour based on position
            t = min(index / 12, 1.0)   # normalise; max effect at segment 12
            r = int(S.COL_SNAKE_BODY[0] * (1 - t) + S.COL_SNAKE_DARK[0] * t)
            g = int(S.COL_SNAKE_BODY[1] * (1 - t) + S.COL_SNAKE_DARK[1] * t)
            b = int(S.COL_SNAKE_BODY[2] * (1 - t) + S.COL_SNAKE_DARK[2] * t)
            colour = (r, g, b)

        # ── Fill segment ───────────────────────────────────────────────────
        pygame.draw.rect(self.screen, colour,
                         (x + pad, y + pad, C - pad * 2, C - pad * 2),
                         border_radius=3)

        # ── Highlight stripe (top-left) ────────────────────────────────────
        hl = (min(colour[0] + 50, 255),
              min(colour[1] + 70, 255),
              min(colour[2] + 30, 255))
        pygame.draw.rect(self.screen, hl,
                         (x + pad, y + pad, C - pad * 2 - 2, 2))

        # ── Head: draw eyes facing the movement direction ──────────────────
        if is_head:
            self._draw_eyes(x, y, direction)

    def _draw_eyes(self, x: int, y: int, direction: tuple) -> None:
        """
        Draw two small eye dots on the head cell, offset toward direction.
        """
        C  = S.CELL
        dx, dy = direction
        cx = x + C // 2
        cy = y + C // 2

        # Push eyes toward the facing edge
        ox = dx * (C // 4)
        oy = dy * (C // 4)

        # Perpendicular offset (for the two eye positions)
        px = dy * (C // 5)   # perpendicular x
        py = dx * (C // 5)   # perpendicular y (note: intentional swap)

        eye_r = 2
        for sign in (-1, 1):
            ex = cx + ox + sign * px
            ey = cy + oy + sign * py
            pygame.draw.circle(self.screen, S.COL_SNAKE_EYE, (ex, ey), eye_r)
            # Pupil
            pygame.draw.circle(self.screen, (0, 0, 0), (ex, ey), 1)

    def _draw_food(self, food: Food) -> None:
        """
        Draw the food pellet as a small pixel-art apple.
        """
        if food.pos is None:
            return

        col, row = food.pos
        C  = S.CELL
        x  = col * C
        y  = row * C
        cx = x + C // 2
        cy = y + C // 2 + 1
        r  = C // 2 - 3

        # Apple body
        pygame.draw.circle(self.screen, S.COL_FOOD, (cx, cy), r)
        # Highlight (top-left)
        pygame.draw.circle(self.screen, S.COL_FOOD_HL, (cx - 2, cy - 2), max(r // 3, 2))
        # Stem (1-px line above centre)
        pygame.draw.line(self.screen, S.COL_FOOD_STEM,
                         (cx, cy - r), (cx + 2, cy - r - 4), 2)
        # Leaf
        pygame.draw.circle(self.screen, S.COL_FOOD_STEM, (cx + 4, cy - r - 3), 2)

    # ── HUD ─────────────────────────────────────────────────────────────────

    def _draw_hud(self, level_sys: LevelSystem) -> None:
        """
        Draw the HUD bar below the game grid showing score and level.
        The level number flashes yellow when a level-up just occurred.
        """
        # HUD sits below the grid; grid ends at ROWS * CELL = WIN_H
        hud_y = S.WIN_H
        hud_w = S.WIN_W

        # Background
        pygame.draw.rect(self.screen, S.COL_HUD_BG, (0, hud_y, hud_w, S.HUD_H))
        # Top border line
        pygame.draw.line(self.screen, S.COL_HUD_BORDER,
                         (0, hud_y), (hud_w, hud_y), 2)

        m = 10  # margin

        # ── Score (left side) ──────────────────────────────────────────────
        label_sc = self._font_small.render("SCORE", True, S.COL_TEXT_DIM)
        value_sc = self._font_big.render(f"{level_sys.score:06d}", True,
                                         S.COL_TEXT_SCORE)
        self.screen.blit(label_sc, (m, hud_y + 4))
        self.screen.blit(value_sc, (m, hud_y + 18))

        # ── Foods eaten this level (centre) ─────────────────────────────────
        # Draw small food-pip indicators (filled = eaten, hollow = remaining)
        pip_cx = hud_w // 2
        pip_y  = hud_y + S.HUD_H // 2
        foods_this = level_sys._foods_this_level
        total_pips = S.FOOD_PER_LEVEL
        pip_r = 5
        pip_gap = 14
        start_x = pip_cx - (total_pips - 1) * pip_gap // 2

        for i in range(total_pips):
            px = start_x + i * pip_gap
            if i < foods_this:
                pygame.draw.circle(self.screen, S.COL_FOOD, (px, pip_y), pip_r)
            else:
                pygame.draw.circle(self.screen, S.COL_TEXT_DIM, (px, pip_y),
                                   pip_r, 1)

        # ── Level (right side) ────────────────────────────────────────────
        # Flash bright yellow during level-up
        if level_sys.level_up_flash > 0 and level_sys.level_up_flash % 8 < 5:
            lv_colour = S.COL_LEVEL_UP
        else:
            lv_colour = S.COL_TEXT_LEVEL

        label_lv = self._font_small.render("LEVEL", True, S.COL_TEXT_DIM)
        value_lv = self._font_big.render(f"{level_sys.level:02d}", True, lv_colour)
        self.screen.blit(label_lv, (hud_w - 70, hud_y + 4))
        self.screen.blit(value_lv, (hud_w - 70, hud_y + 18))

    # ── Level-up banner ──────────────────────────────────────────────────────

    def _draw_level_up_banner(self, level_sys: LevelSystem) -> None:
        """
        Draw a centred 'LEVEL UP!' banner while the flash timer is active.
        Fades in/out using alpha.
        """
        if level_sys.level_up_flash <= 0:
            return

        # Alpha: fade in quickly, hold, fade out
        t = level_sys.level_up_flash
        alpha = min(255, t * 10)   # fade out during last ~25 frames

        surf = self._font_huge.render("LEVEL  UP!", True, S.COL_LEVEL_UP)
        surf.set_alpha(alpha)
        rect = surf.get_rect(center=(S.WIN_W // 2, S.WIN_H // 2))
        self.screen.blit(surf, rect)

        # Subtitle: current speed
        spd_txt = self._font_med.render(
            f"SPEED  {level_sys.speed:.1f}", True, S.COL_WHITE)
        spd_txt.set_alpha(alpha)
        self.screen.blit(spd_txt,
                         spd_txt.get_rect(center=(S.WIN_W // 2, S.WIN_H // 2 + 52)))

    # ── Main public draw method ──────────────────────────────────────────────

    def draw_frame(self, snake: Snake, food: Food,
                   level_sys: LevelSystem) -> None:
        """
        Render a complete game frame:
          1. Background fill
          2. Faint grid
          3. Wall border
          4. Food pellet
          5. Snake body
          6. HUD bar
          7. Level-up banner (if active)
        """
        # 1. Background
        self.screen.fill(S.COL_BG)

        # 2. Grid overlay
        self.screen.blit(self._grid_surf, (0, 0))

        # 3. Wall border
        self.screen.blit(self._wall_surf, (0, 0))

        # 4. Food
        self._draw_food(food)

        # 5. Snake — draw tail-to-head so the head renders on top
        body = snake.body
        for i in range(len(body) - 1, -1, -1):
            col, row = body[i]
            is_head  = (i == 0)
            self._draw_snake_segment(col, row, is_head, snake.dir, i)

        # 6. HUD
        self._draw_hud(level_sys)

        # 7. Level-up banner
        self._draw_level_up_banner(level_sys)

    # ── Game Over overlay ────────────────────────────────────────────────────

    def draw_game_over(self, level_sys: LevelSystem) -> None:
        """
        Draw a semi-transparent overlay with final score, level, and controls.
        """
        # Dark vignette
        overlay = pygame.Surface((S.WIN_W, S.WIN_H + S.HUD_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        cx = S.WIN_W // 2
        cy = S.WIN_H // 2

        # "GAME OVER"
        go = self._font_huge.render("GAME OVER", True, S.COL_GAMEOVER_TXT)
        self.screen.blit(go, go.get_rect(centerx=cx, centery=cy - 70))

        # Score
        sc = self._font_big.render(
            f"SCORE   {level_sys.score:06d}", True, S.COL_TEXT_SCORE)
        self.screen.blit(sc, sc.get_rect(centerx=cx, centery=cy))

        # Level reached
        lv = self._font_big.render(
            f"LEVEL   {level_sys.level:02d}", True, S.COL_TEXT_LEVEL)
        self.screen.blit(lv, lv.get_rect(centerx=cx, centery=cy + 34))

        # Foods eaten
        fe = self._font_med.render(
            f"APPLES  {level_sys.foods_eaten}", True, S.COL_TEXT_DIM)
        self.screen.blit(fe, fe.get_rect(centerx=cx, centery=cy + 66))

        # Controls
        r  = self._font_small.render("PRESS  R  TO  RESTART", True, S.COL_WHITE)
        q  = self._font_small.render("PRESS  Q  TO  QUIT",    True, (140, 140, 140))
        self.screen.blit(r, r.get_rect(centerx=cx, centery=cy + 108))
        self.screen.blit(q, q.get_rect(centerx=cx, centery=cy + 128))
