"""
renderer.py
===========
Pygame rendering for all game screens — TSIS 4 edition.

Screens rendered
----------------
  draw_frame()        — in-game HUD + grid + snake + food + powerups + obstacles
  draw_game_over()    — game-over overlay
  draw_menu()         — main menu (username input, buttons)
  draw_leaderboard()  — top-10 table
  draw_settings()     — settings panel
"""

import math
import pygame
import config as C


# ════════════════════════════════════════════════════════════════════════════
#  Renderer
# ════════════════════════════════════════════════════════════════════════════

class Renderer:
    """
    Owns all Pygame drawing operations.

    The screen surface is passed in; the renderer never creates its own window.
    Static surfaces (wall tiles, grid) are baked once in __init__ for speed.
    """

    def __init__(self, screen: pygame.Surface, prefs: dict):
        self.screen = screen
        self.prefs  = prefs                # live reference to preferences dict

        # ── Fonts ──────────────────────────────────────────────────────────
        pygame.font.init()
        self.font_hud    = pygame.font.SysFont("Consolas,Courier New,monospace", 15, bold=True)
        self.font_big    = pygame.font.SysFont("Consolas,Courier New,monospace", 28, bold=True)
        self.font_xl     = pygame.font.SysFont("Consolas,Courier New,monospace", 46, bold=True)
        self.font_small  = pygame.font.SysFont("Consolas,Courier New,monospace", 13)
        self.font_title  = pygame.font.SysFont("Consolas,Courier New,monospace", 36, bold=True)
        self.font_symbol = pygame.font.SysFont("Segoe UI Symbol,DejaVu Sans,monospace", 14, bold=True)

        # ── Pre-baked surfaces ─────────────────────────────────────────────
        self._wall_surf = self._bake_walls()
        self._grid_surf = self._bake_grid()

    # ── Baking ────────────────────────────────────────────────────────────────

    def _bake_walls(self) -> pygame.Surface:
        surf = pygame.Surface((C.WIN_W, C.WIN_H), pygame.SRCALPHA)
        t = C.WALL_THICKNESS
        for col in range(C.COLS):
            for row in range(C.ROWS):
                if col < t or col >= C.COLS - t or row < t or row >= C.ROWS - t:
                    self._draw_wall_cell(surf, col, row)
        return surf

    def _draw_wall_cell(self, surf: pygame.Surface, col: int, row: int) -> None:
        x = col * C.CELL
        y = row * C.CELL
        pygame.draw.rect(surf, C.COL_WALL,    (x, y, C.CELL, C.CELL))
        pygame.draw.rect(surf, C.COL_WALL_HL, (x, y, C.CELL - 1, C.CELL - 1), 1)

    def _bake_grid(self) -> pygame.Surface:
        surf = pygame.Surface((C.WIN_W, C.WIN_H), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        for col in range(C.PLAY_LEFT, C.PLAY_RIGHT + 2):
            x = col * C.CELL
            pygame.draw.line(surf, C.COL_GRID, (x, C.PLAY_TOP * C.CELL),
                             (x, (C.PLAY_BOTTOM + 1) * C.CELL))
        for row in range(C.PLAY_TOP, C.PLAY_BOTTOM + 2):
            y = row * C.CELL
            pygame.draw.line(surf, C.COL_GRID, (C.PLAY_LEFT * C.CELL, y),
                             ((C.PLAY_RIGHT + 1) * C.CELL, y))
        return surf

    # ── Utility ───────────────────────────────────────────────────────────────

    def _cell_rect(self, col: int, row: int, inset: int = 0) -> pygame.Rect:
        return pygame.Rect(
            col * C.CELL + inset,
            row * C.CELL + inset,
            C.CELL - 2 * inset,
            C.CELL - 2 * inset,
        )

    def _text(self, surf: pygame.Surface, msg: str, font, color: tuple,
              x: int, y: int, anchor: str = "topleft") -> pygame.Rect:
        img = font.render(msg, True, color)
        r   = img.get_rect(**{anchor: (x, y)})
        surf.blit(img, r)
        return r

    # ════════════════════════════════════════════════════════════════════════
    #  In-game frame
    # ════════════════════════════════════════════════════════════════════════

    def draw_frame(self, snake, food_mgr, level_sys, powerup_mgr,
                   obstacle_mgr, personal_best: int) -> None:
        s = self.screen
        s.fill(C.COL_BG)

        # Grid (optional)
        if self.prefs.get("grid", True):
            s.blit(self._grid_surf, (0, 0))

        # Walls
        s.blit(self._wall_surf, (0, 0))

        # Obstacles
        self._draw_obstacles(s, obstacle_mgr)

        # Food
        for item in food_mgr.items:
            self._draw_food(s, item)

        # Power-up field item
        if powerup_mgr.field_item:
            self._draw_powerup_item(s, powerup_mgr.field_item)

        # Snake
        self._draw_snake(s, snake)

        # HUD
        self._draw_hud(s, snake, level_sys, powerup_mgr, food_mgr, personal_best)

        # Level-up banner
        if level_sys.level_up_flash > 0:
            self._draw_level_banner(s, level_sys.level)

    # ── Obstacles ────────────────────────────────────────────────────────────

    def _draw_obstacles(self, s: pygame.Surface, obstacle_mgr) -> None:
        for (col, row) in obstacle_mgr.blocks:
            x = col * C.CELL
            y = row * C.CELL
            pygame.draw.rect(s, C.COL_OBSTACLE, (x, y, C.CELL, C.CELL))
            # 3-D bevel
            pygame.draw.line(s, C.COL_OBSTACLE_HL, (x, y), (x + C.CELL - 1, y))
            pygame.draw.line(s, C.COL_OBSTACLE_HL, (x, y), (x, y + C.CELL - 1))
            pygame.draw.line(s, (30, 30, 50),
                             (x + C.CELL - 1, y), (x + C.CELL - 1, y + C.CELL - 1))
            pygame.draw.line(s, (30, 30, 50),
                             (x, y + C.CELL - 1), (x + C.CELL - 1, y + C.CELL - 1))

    # ── Food ─────────────────────────────────────────────────────────────────

    def _draw_food(self, s: pygame.Surface, item) -> None:
        col, row = item.pos
        now_ms   = pygame.time.get_ticks()

        # Blinking: hide every other 200 ms when close to expiry
        if item.is_blinking and (now_ms // 200) % 2 == 0:
            return

        cx = col * C.CELL + C.CELL // 2
        cy = row * C.CELL + C.CELL // 2
        r  = C.CELL // 2 - 2

        cfg = item.config
        if cfg.is_poison:
            self._draw_poison_food(s, col, row, cx, cy, r, cfg, item)
        else:
            self._draw_normal_food(s, col, row, cx, cy, r, cfg, item)

    def _draw_normal_food(self, s, col, row, cx, cy, r, cfg, item) -> None:
        # Timer arc
        frac = item.lifetime_fraction
        start_angle = -math.pi / 2
        end_angle   = start_angle + 2 * math.pi * frac
        arc_r = pygame.Rect(col * C.CELL + 1, row * C.CELL + 1,
                            C.CELL - 2, C.CELL - 2)
        if frac > 0.01:
            pygame.draw.arc(s, cfg.col_timer, arc_r, start_angle, end_angle, 2)

        # Body circle
        pygame.draw.circle(s, cfg.col_body, (cx, cy), r)
        # Highlight
        pygame.draw.circle(s, cfg.col_highlight, (cx - r // 3, cy - r // 3), r // 4)
        # Stem
        pygame.draw.line(s, cfg.col_stem, (cx, cy - r), (cx, cy - r - 4), 2)

    def _draw_poison_food(self, s, col, row, cx, cy, r, cfg, item) -> None:
        frac = item.lifetime_fraction
        # Dark red skull-like shape (diamond)
        pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(s, cfg.col_body, pts)
        pygame.draw.polygon(s, cfg.col_highlight, pts, 1)
        # Crossbones "X" marks
        d = r // 2
        pygame.draw.line(s, cfg.col_highlight,
                         (cx - d, cy - d), (cx + d, cy + d), 2)
        pygame.draw.line(s, cfg.col_highlight,
                         (cx + d, cy - d), (cx - d, cy + d), 2)
        # Countdown ring
        if frac > 0.01:
            arc_r = pygame.Rect(col * C.CELL + 1, row * C.CELL + 1,
                                C.CELL - 2, C.CELL - 2)
            end_a = -math.pi / 2 + 2 * math.pi * frac
            pygame.draw.arc(s, cfg.col_timer, arc_r, -math.pi / 2, end_a, 2)

    # ── Power-up field item ───────────────────────────────────────────────────

    def _draw_powerup_item(self, s: pygame.Surface, pu) -> None:
        col, row = pu.pos
        now_ms   = pygame.time.get_ticks()

        # Blink when less than 25 % life left
        if pu.lifetime_fraction < 0.25 and (now_ms // 200) % 2 == 0:
            return

        cx = col * C.CELL + C.CELL // 2
        cy = row * C.CELL + C.CELL // 2
        r  = C.CELL // 2 - 2

        # Pulsing glow
        pulse = 0.6 + 0.4 * math.sin(now_ms / 200.0)
        glow_col = tuple(int(c * pulse) for c in pu.config.col_glow)
        pygame.draw.circle(s, glow_col, (cx, cy), r + 3)
        pygame.draw.circle(s, pu.config.col_body, (cx, cy), r)

        # Countdown arc
        frac = pu.lifetime_fraction
        if frac > 0.01:
            arc_r = pygame.Rect(col * C.CELL, row * C.CELL, C.CELL, C.CELL)
            end_a = -math.pi / 2 + 2 * math.pi * frac
            pygame.draw.arc(s, C.COL_WHITE, arc_r, -math.pi / 2, end_a, 2)

        # Symbol
        sym = self.font_symbol.render(pu.config.symbol, True, C.COL_BG)
        s.blit(sym, sym.get_rect(center=(cx, cy)))

    # ── Snake ─────────────────────────────────────────────────────────────────

    def _draw_snake(self, s: pygame.Surface, snake) -> None:
        snake_color = self.prefs.get("snake_color", list(C.COL_SNAKE_BODY))
        body_col = tuple(snake_color)
        head_col = tuple(min(255, c + 80) for c in body_col)
        dark_col = tuple(max(0, c - 60) for c in body_col)

        for i, (col, row) in enumerate(snake.body):
            is_head = (i == 0)
            color   = head_col if is_head else (body_col if i % 2 == 0 else dark_col)
            rect    = self._cell_rect(col, row, 1)
            pygame.draw.rect(s, color, rect, border_radius=3)

            if is_head:
                # Eyes
                dx, dy  = snake.dir
                ex = col * C.CELL + C.CELL // 2 + dx * 4
                ey = row * C.CELL + C.CELL // 2 + dy * 4
                perp = (-dy, dx)
                pygame.draw.circle(s, C.COL_SNAKE_EYE,
                                   (ex + perp[0] * 3, ey + perp[1] * 3), 2)
                pygame.draw.circle(s, C.COL_SNAKE_EYE,
                                   (ex - perp[0] * 3, ey - perp[1] * 3), 2)

        # Shield glow
        if snake.shield:
            hcol, hrow = snake.head
            cx = hcol * C.CELL + C.CELL // 2
            cy = hrow * C.CELL + C.CELL // 2
            t  = pygame.time.get_ticks()
            a  = int(128 + 80 * math.sin(t / 100.0))
            glow = pygame.Surface((C.CELL + 8, C.CELL + 8), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*C.COL_SHIELD_ACTIVE, a),
                               (C.CELL // 2 + 4, C.CELL // 2 + 4), C.CELL // 2 + 3)
            s.blit(glow, (cx - C.CELL // 2 - 4, cy - C.CELL // 2 - 4))

    # ── HUD ───────────────────────────────────────────────────────────────────

    def _draw_hud(self, s: pygame.Surface, snake, level_sys, powerup_mgr,
                  food_mgr, personal_best: int) -> None:
        hy = C.WIN_H
        pygame.draw.rect(s, C.COL_HUD_BG, (0, hy, C.WIN_W, C.HUD_H))
        pygame.draw.line(s, C.COL_HUD_BORDER, (0, hy), (C.WIN_W, hy), 1)

        # Score
        self._text(s, f"SCORE {level_sys.score:>6}", self.font_hud,
                   C.COL_TEXT_SCORE, 8, hy + 6)
        # Level
        self._text(s, f"LVL {level_sys.level}", self.font_hud,
                   C.COL_TEXT_LEVEL, 160, hy + 6)
        # Length
        self._text(s, f"LEN {len(snake.body)}", self.font_hud,
                   C.COL_TEXT_DIM, 230, hy + 6)
        # Personal best
        self._text(s, f"BEST {personal_best:>6}", self.font_hud,
                   C.COL_PERSONAL_BEST, 310, hy + 6)
        # Shield indicator
        if snake.shield:
            self._text(s, "★ SHIELD", self.font_hud,
                       C.COL_SHIELD_ACTIVE, 8, hy + 26)

        # Active power-up indicator
        if powerup_mgr.active_config:
            remaining = f"{powerup_mgr.effect_remaining_s:.1f}s"
            name = powerup_mgr.active_config.name
            col  = powerup_mgr.active_config.col_body
            msg  = f"[{name} {remaining}]"
            self._text(s, msg, self.font_hud, col, C.WIN_W // 2, hy + 16, "center")

        # Food type dots (HUD indicator)
        dot_x = C.WIN_W - 12
        for item in food_mgr.items:
            pygame.draw.circle(s, item.config.col_body, (dot_x, hy + 24), 5)
            dot_x -= 14

    # ── Level-up banner ───────────────────────────────────────────────────────

    def _draw_level_banner(self, s: pygame.Surface, level: int) -> None:
        msg  = f"  LEVEL {level}!  "
        surf = self.font_big.render(msg, True, C.COL_LEVEL_UP)
        r    = surf.get_rect(center=(C.WIN_W // 2, C.WIN_H // 2 - 20))
        bg   = pygame.Surface((r.w + 20, r.h + 10))
        bg.fill((20, 20, 0))
        s.blit(bg, (r.x - 10, r.y - 5))
        s.blit(surf, r)

    # ════════════════════════════════════════════════════════════════════════
    #  Game-over overlay
    # ════════════════════════════════════════════════════════════════════════

    def draw_game_over(self, level_sys, personal_best: int) -> None:
        s = self.screen

        # Dark overlay
        overlay = pygame.Surface((C.WIN_W, C.WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        s.blit(overlay, (0, 0))

        cy = C.WIN_H // 2 - 70
        self._text(s, "GAME  OVER", self.font_xl, C.COL_GAMEOVER_TXT,
                   C.WIN_W // 2, cy, "center")
        self._text(s, f"Score : {level_sys.score}", self.font_big, C.COL_TEXT_SCORE,
                   C.WIN_W // 2, cy + 60, "center")
        self._text(s, f"Level : {level_sys.level}", self.font_big, C.COL_TEXT_LEVEL,
                   C.WIN_W // 2, cy + 95, "center")
        self._text(s, f"Best  : {personal_best}", self.font_big, C.COL_PERSONAL_BEST,
                   C.WIN_W // 2, cy + 130, "center")

        self._draw_button(s, "[ R ]  RETRY",    C.WIN_W // 2, cy + 185, "center")
        self._draw_button(s, "[ M ]  MAIN MENU", C.WIN_W // 2, cy + 215, "center")
        self._draw_button(s, "[ Q ]  QUIT",      C.WIN_W // 2, cy + 245, "center")

    def _draw_button(self, s, label, x, y, anchor="topleft", selected=False):
        col = C.COL_MENU_BTN_SEL if selected else C.COL_TEXT_DIM
        self._text(s, label, self.font_hud, col, x, y, anchor)

    # ════════════════════════════════════════════════════════════════════════
    #  Main Menu
    # ════════════════════════════════════════════════════════════════════════

    def draw_menu(self, username: str, cursor_visible: bool,
                  selected_btn: int) -> None:
        s = self.screen
        s.fill(C.COL_MENU_BG)

        # Title
        self._text(s, "PIXEL SNAKE", self.font_xl, C.COL_SNAKE_HEAD,
                   C.WIN_W // 2, 60, "center")
        self._text(s, "TSIS 4", self.font_hud, C.COL_TEXT_DIM,
                   C.WIN_W // 2, 115, "center")

        # Username box
        self._text(s, "PLAYER NAME:", self.font_hud, C.COL_TEXT_DIM,
                   C.WIN_W // 2 - 140, 175)
        box_rect = pygame.Rect(C.WIN_W // 2 - 140, 195, 280, 32)
        pygame.draw.rect(s, (20, 40, 20), box_rect)
        pygame.draw.rect(s, C.COL_WALL_HL, box_rect, 1)
        display_name = username + ("|" if cursor_visible else " ")
        self._text(s, display_name, self.font_hud, C.COL_WHITE,
                   box_rect.x + 6, box_rect.y + 8)

        # Buttons
        buttons = ["PLAY", "LEADERBOARD", "SETTINGS", "QUIT"]
        for i, label in enumerate(buttons):
            y   = 260 + i * 48
            sel = (i == selected_btn)
            col = C.COL_MENU_BTN_SEL if sel else C.COL_MENU_BTN
            br  = pygame.Rect(C.WIN_W // 2 - 110, y, 220, 36)
            pygame.draw.rect(s, col, br, border_radius=6)
            pygame.draw.rect(s, C.COL_WALL_HL, br, 1, border_radius=6)
            self._text(s, label, self.font_hud, C.COL_MENU_BTN_TXT,
                       C.WIN_W // 2, y + 10, "center")

        self._text(s, "↑↓ navigate  ·  ENTER select  ·  type username",
                   self.font_small, C.COL_TEXT_DIM, C.WIN_W // 2,
                   C.TOTAL_H - 20, "center")

    # ════════════════════════════════════════════════════════════════════════
    #  Leaderboard
    # ════════════════════════════════════════════════════════════════════════

    def draw_leaderboard(self, rows: list[dict]) -> None:
        s = self.screen
        s.fill(C.COL_MENU_BG)

        self._text(s, "LEADERBOARD", self.font_title, C.COL_TEXT_SCORE,
                   C.WIN_W // 2, 18, "center")
        pygame.draw.line(s, C.COL_HUD_BORDER, (20, 58), (C.WIN_W - 20, 58), 1)

        # Header
        hx = [24, 60, 160, 280, 370]
        hdrs = ["#", "PLAYER", "SCORE", "LVL", "DATE"]
        hcols = [C.COL_TEXT_DIM] * 5
        for hdr, x, col in zip(hdrs, hx, hcols):
            self._text(s, hdr, self.font_hud, col, x, 64)

        pygame.draw.line(s, C.COL_HUD_BORDER, (20, 82), (C.WIN_W - 20, 82), 1)

        if not rows:
            self._text(s, "No results yet — play a game first!",
                       self.font_hud, C.COL_TEXT_DIM, C.WIN_W // 2, 180, "center")
        else:
            for i, row in enumerate(rows):
                y = 88 + i * 26
                rank_col = {1: (255, 215, 0), 2: (192, 192, 192),
                             3: (205, 127, 50)}.get(int(row["rank"]), C.COL_TEXT_DIM)
                date_str = row["played_at"].strftime("%m/%d %H:%M") \
                    if hasattr(row.get("played_at", ""), "strftime") else str(row.get("played_at", ""))[:10]
                values = [
                    str(row["rank"]),
                    str(row["username"])[:12],
                    str(row["score"]),
                    str(row["level"]),
                    date_str,
                ]
                colors = [rank_col, C.COL_WHITE, C.COL_TEXT_SCORE,
                          C.COL_TEXT_LEVEL, C.COL_TEXT_DIM]
                for val, x, col in zip(values, hx, colors):
                    self._text(s, val, self.font_small, col, x, y)

        pygame.draw.line(s, C.COL_HUD_BORDER,
                         (20, C.TOTAL_H - 40), (C.WIN_W - 20, C.TOTAL_H - 40), 1)
        self._text(s, "[ B ] BACK  ·  [ Q ] QUIT", self.font_hud, C.COL_TEXT_DIM,
                   C.WIN_W // 2, C.TOTAL_H - 28, "center")

    # ════════════════════════════════════════════════════════════════════════
    #  Settings
    # ════════════════════════════════════════════════════════════════════════

    def draw_settings(self, prefs: dict, selected: int) -> None:
        s = self.screen
        s.fill(C.COL_MENU_BG)

        self._text(s, "SETTINGS", self.font_title, C.COL_TEXT_SCORE,
                   C.WIN_W // 2, 18, "center")
        pygame.draw.line(s, C.COL_HUD_BORDER, (20, 58), (C.WIN_W - 20, 58), 1)

        items = [
            ("Grid overlay",  "grid",        "ON" if prefs.get("grid", True) else "OFF"),
            ("Sound",         "sound",       "ON" if prefs.get("sound", True) else "OFF"),
            ("Snake color",   "snake_color", self._color_label(prefs.get("snake_color", [40, 180, 40]))),
        ]

        for i, (label, key, val) in enumerate(items):
            y   = 90 + i * 60
            sel = (i == selected)
            br  = pygame.Rect(30, y, C.WIN_W - 60, 44)
            pygame.draw.rect(s, C.COL_MENU_BTN_SEL if sel else C.COL_MENU_BTN,
                             br, border_radius=6)
            pygame.draw.rect(s, C.COL_WALL_HL, br, 1, border_radius=6)

            self._text(s, label, self.font_hud, C.COL_WHITE, br.x + 14, br.y + 14)
            self._text(s, val,   self.font_hud, C.COL_TEXT_SCORE,
                       br.right - 14, br.y + 14, "topright")

            # Color swatch
            if key == "snake_color":
                swatch = pygame.Rect(br.right - 80, br.y + 10, 24, 24)
                pygame.draw.rect(s, tuple(prefs.get("snake_color", [40, 180, 40])),
                                 swatch, border_radius=3)
                pygame.draw.rect(s, C.COL_WHITE, swatch, 1, border_radius=3)

        self._text(s, "↑↓ navigate  ·  LEFT/RIGHT change  ·  ENTER/SPACE toggle",
                   self.font_small, C.COL_TEXT_DIM, C.WIN_W // 2, 290, "center")
        pygame.draw.line(s, C.COL_HUD_BORDER,
                         (20, C.TOTAL_H - 40), (C.WIN_W - 20, C.TOTAL_H - 40), 1)
        self._text(s, "[ S ] SAVE & BACK  ·  [ B ] BACK WITHOUT SAVING",
                   self.font_hud, C.COL_TEXT_DIM,
                   C.WIN_W // 2, C.TOTAL_H - 28, "center")

    @staticmethod
    def _color_label(rgb) -> str:
        presets = {
            (40, 180, 40):   "GREEN",
            (80, 160, 255):  "BLUE",
            (255, 80, 80):   "RED",
            (255, 200, 0):   "GOLD",
            (200, 100, 255): "PURPLE",
        }
        key = tuple(rgb)
        return presets.get(key, f"#{key[0]:02X}{key[1]:02X}{key[2]:02X}")
