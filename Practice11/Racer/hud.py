"""
hud.py
======
Heads-Up Display renderer for PIXEL RACER.

Panels
------
Top-left   : SCORE and road SPEED
Top-right  : coin count + weighted coin VALUE + last-pickup indicator
Centre     : "DANGER! ENEMY SPEED UP" warning flash (when enemy boost fires)

Also renders the Game Over overlay with final stats.
"""

import pygame
import settings as S


class HUD:
    """
    Draws all on-screen stats each frame.
    Instantiate once; call draw() every frame.
    """

    def __init__(self):
        # ── Fonts (chunky monospace for the retro terminal feel) ──────────
        try:
            self._font_big   = pygame.font.SysFont("monospace", 20, bold=True)
            self._font_med   = pygame.font.SysFont("monospace", 16, bold=True)
            self._font_small = pygame.font.SysFont("monospace", 13, bold=True)
            self._font_huge  = pygame.font.SysFont("monospace", 48, bold=True)
            self._font_danger= pygame.font.SysFont("monospace", 26, bold=True)
        except Exception:
            self._font_big   = pygame.font.Font(None, 24)
            self._font_med   = pygame.font.Font(None, 20)
            self._font_small = pygame.font.Font(None, 16)
            self._font_huge  = pygame.font.Font(None, 54)
            self._font_danger= pygame.font.Font(None, 30)

        # ── Semi-transparent panel backgrounds ────────────────────────────
        self._panel_left  = self._make_panel(170, 56)
        self._panel_right = self._make_panel(155, 56)

    @staticmethod
    def _make_panel(w: int, h: int) -> pygame.Surface:
        """Return a dark semi-transparent rectangle surface."""
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 155))
        return s

    # ── Main draw call ────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface, score: int, speed: float,
             coins_count: int, coin_value: int,
             last_coin_type: dict | None,
             danger_flash: int, enemy_extra: float) -> None:
        """
        Render all HUD elements onto screen.

        Parameters
        ----------
        score           : total accumulated score
        speed           : current road scroll speed (px/frame)
        coins_count     : total coins collected (used for boost threshold display)
        coin_value      : total weighted value earned from all collected coins
        last_coin_type  : the COIN_TYPES dict of the most recently collected coin,
                          or None if no coin has been collected yet.
        danger_flash    : countdown timer for the danger warning (0 = not showing)
        enemy_extra     : current enemy extra speed — shown as a "tier" indicator
        """
        m = S.HUD_MARGIN

        # ── Left panel: SCORE + SPEED ─────────────────────────────────────
        screen.blit(self._panel_left, (m, m))

        score_surf = self._font_big.render(f"SCORE {score:06d}", True,
                                           S.COL_HUD_TEXT)
        speed_surf = self._font_small.render(f"SPEED  {speed:.1f}", True,
                                             S.COL_SCORE_TEXT)
        screen.blit(score_surf, (m + 4, m + 4))
        screen.blit(speed_surf, (m + 4, m + 32))

        # Enemy speed tier (small indicator below speed)
        tier = self._enemy_tier_label(enemy_extra)
        tier_col = self._tier_colour(enemy_extra)
        tier_surf = self._font_small.render(tier, True, tier_col)
        screen.blit(tier_surf, (m + 4, m + 44))

        # ── Right panel: COINS count + VALUE + last pickup ────────────────
        panel_x = S.WIN_W - 155 - m
        screen.blit(self._panel_right, (panel_x, m))

        # "COINS" label
        lbl = self._font_small.render("COINS", True, S.COL_SCORE_TEXT)
        screen.blit(lbl, (panel_x + 4, m + 2))

        # Coin count (number of coins collected)
        cnt_surf = self._font_big.render(f"x{coins_count:03d}", True,
                                         S.COL_COIN_TEXT)
        screen.blit(cnt_surf, (panel_x + 4, m + 16))

        # Weighted value earned (shown in the type's label colour)
        val_col  = last_coin_type["label_color"] if last_coin_type else S.COL_SCORE_TEXT
        val_surf = self._font_small.render(f"PTS {coin_value:04d}", True, val_col)
        screen.blit(val_surf, (panel_x + 4, m + 40))

        # Last-coin type badge (e.g. "★ GEM") with rarity colour
        if last_coin_type:
            badge = self._font_small.render(
                f"▶ {last_coin_type['name'].upper()}", True,
                last_coin_type["label_color"]
            )
            screen.blit(badge, (panel_x + 72, m + 40))

        # ── Danger flash: ENEMY SPEED UP ─────────────────────────────────
        if danger_flash > 0:
            self._draw_danger_banner(screen, danger_flash)

    # ── Danger banner ──────────────────────────────────────────────────────────

    def _draw_danger_banner(self, screen: pygame.Surface, timer: int) -> None:
        """
        Draw a centred, pulsing "DANGER! ENEMY SPEED UP" warning.
        The banner alternates bright/dark to create a strobe effect.
        Alpha fades out over the last 30 frames of the timer.
        """
        # Strobe: bright every other 8-frame block
        bright = (timer // 8) % 2 == 0
        colour = S.COL_DANGER if bright else S.COL_DANGER_DIM

        # Alpha: fully opaque for most of the duration, then fade out
        alpha  = min(255, timer * 5)

        line1 = self._font_danger.render("⚠  DANGER!  ⚠", True, colour)
        line2 = self._font_med.render("ENEMY  SPEED  UP", True, S.COL_WHITE)
        line1.set_alpha(alpha)
        line2.set_alpha(alpha)

        cx = S.WIN_W // 2
        # Position banner in the upper-middle of the road
        screen.blit(line1, line1.get_rect(centerx=cx, centery=120))
        screen.blit(line2, line2.get_rect(centerx=cx, centery=152))

    # ── Enemy tier helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _enemy_tier_label(extra: float) -> str:
        """Return a short text label for the current enemy extra speed."""
        if extra <= S.ENEMY_SPEED_EXTRA:
            return "ENEMY ░░░░"          # baseline
        boosts = round((extra - S.ENEMY_SPEED_EXTRA) / S.ENEMY_BOOST_AMOUNT)
        filled = min(boosts, 4)
        bar    = "█" * filled + "░" * (4 - filled)
        return f"ENEMY {bar}"

    @staticmethod
    def _tier_colour(extra: float) -> tuple:
        """Colour the enemy tier label from green → yellow → red as it grows."""
        ratio = (extra - S.ENEMY_SPEED_EXTRA) / max(
            1, S.ENEMY_SPEED_EXTRA_MAX - S.ENEMY_SPEED_EXTRA
        )
        ratio = max(0.0, min(1.0, ratio))
        r = int(255 * ratio)
        g = int(255 * (1 - ratio))
        return (r, g, 0)

    # ── Game Over overlay ──────────────────────────────────────────────────────

    def draw_game_over(self, screen: pygame.Surface, score: int,
                       coins_count: int, coin_value: int) -> None:
        """
        Full-screen semi-transparent overlay with final stats.
        Shows score, coins collected, weighted value earned, and controls.
        """
        # Dark vignette
        overlay = pygame.Surface((S.WIN_W, S.WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        screen.blit(overlay, (0, 0))

        cx = S.WIN_W // 2

        # "GAME OVER"
        go = self._font_huge.render("GAME OVER", True, S.COL_GAME_OVER)
        screen.blit(go, go.get_rect(centerx=cx, centery=190))

        # Score
        sc = self._font_big.render(f"SCORE  : {score:06d}", True, S.COL_HUD_TEXT)
        screen.blit(sc, sc.get_rect(centerx=cx, centery=265))

        # Coins collected
        co = self._font_big.render(f"COINS  : {coins_count:03d}", True,
                                   S.COL_COIN_TEXT)
        screen.blit(co, co.get_rect(centerx=cx, centery=295))

        # Weighted coin value
        vl = self._font_big.render(f"VALUE  : {coin_value:04d}", True,
                                   (200, 240, 200))
        screen.blit(vl, vl.get_rect(centerx=cx, centery=325))

        # Controls
        r_hint = self._font_small.render("PRESS  R  TO  RESTART", True,
                                          S.COL_WHITE)
        q_hint = self._font_small.render("PRESS  Q  TO  QUIT", True,
                                          (160, 160, 160))
        screen.blit(r_hint, r_hint.get_rect(centerx=cx, centery=390))
        screen.blit(q_hint, q_hint.get_rect(centerx=cx, centery=412))
