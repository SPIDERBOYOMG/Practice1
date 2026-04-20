"""
hud.py
======
Heads-Up Display (HUD) rendering for the Racer game.
Draws the score, speed, and coin count each frame.
Keeps all draw calls in one place so main.py stays clean.
"""

import pygame
import settings as S


class HUD:
    """
    Renders the on-screen stats panel each frame.

    Draws two panels:
      • Top-left  – current score (distance driven) and speed level
      • Top-right – coin icon + collected coin count
    """

    def __init__(self, coin_image: pygame.Surface):
        # Load a chunky monospace-style font; fall back to default if unavailable
        try:
            self._font_big   = pygame.font.SysFont("monospace", 20, bold=True)
            self._font_small = pygame.font.SysFont("monospace", 14, bold=True)
        except Exception:
            self._font_big   = pygame.font.Font(None, 24)
            self._font_small = pygame.font.Font(None, 18)

        # Scale the coin image for the HUD badge
        self._coin_icon = pygame.transform.scale(coin_image, (20, 20))

        # Semi-transparent panel surface (reused each frame)
        self._panel_left  = pygame.Surface((160, 52), pygame.SRCALPHA)
        self._panel_right = pygame.Surface((120, 52), pygame.SRCALPHA)
        for p in (self._panel_left, self._panel_right):
            p.fill((0, 0, 0, 150))   # dark translucent

    def draw(self, screen: pygame.Surface,
             score: int, speed: float, coins: int) -> None:
        """
        Blit all HUD elements onto 'screen'.
        Call this once per frame after all other rendering.
        """
        m = S.HUD_MARGIN   # shorthand margin

        # ── Left panel: SCORE & SPEED ──────────────────────────────────────
        screen.blit(self._panel_left, (m, m))

        score_surf = self._font_big.render(f"SCORE {score:06d}", True,
                                           S.COL_HUD_TEXT)
        speed_surf = self._font_small.render(f"SPEED  {speed:.1f}", True,
                                             S.COL_SCORE_TEXT)
        screen.blit(score_surf, (m + 4, m + 4))
        screen.blit(speed_surf, (m + 4, m + 30))

        # ── Right panel: COIN COUNTER ──────────────────────────────────────
        panel_x = S.WIN_W - 120 - m
        screen.blit(self._panel_right, (panel_x, m))

        # Coin icon
        screen.blit(self._coin_icon, (panel_x + 6, m + 16))

        # Coin count text  "× 000"
        coin_surf = self._font_big.render(f"x{coins:03d}", True,
                                          S.COL_COIN_TEXT)
        screen.blit(coin_surf, (panel_x + 32, m + 14))

        # Small "COINS" label above
        label = self._font_small.render("COINS", True, S.COL_SCORE_TEXT)
        screen.blit(label, (panel_x + 30, m + 2))

    def draw_game_over(self, screen: pygame.Surface,
                       score: int, coins: int) -> None:
        """
        Overlay the GAME OVER screen centred on the window.
        Shows final score and total coins collected.
        """
        # Dark overlay
        overlay = pygame.Surface((S.WIN_W, S.WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        cx = S.WIN_W // 2

        # "GAME OVER" banner
        go_font = pygame.font.SysFont("monospace", 48, bold=True)
        go_surf = go_font.render("GAME OVER", True, S.COL_GAME_OVER)
        screen.blit(go_surf, go_surf.get_rect(centerx=cx, centery=200))

        # Final score
        sc_surf = self._font_big.render(f"SCORE : {score:06d}", True,
                                        S.COL_HUD_TEXT)
        screen.blit(sc_surf, sc_surf.get_rect(centerx=cx, centery=280))

        # Coins collected
        co_surf = self._font_big.render(f"COINS : {coins:03d}", True,
                                        S.COL_COIN_TEXT)
        screen.blit(co_surf, co_surf.get_rect(centerx=cx, centery=315))

        # Restart hint
        hint = self._font_small.render("PRESS  R  TO  RESTART", True,
                                       S.COL_WHITE)
        screen.blit(hint, hint.get_rect(centerx=cx, centery=380))

        quit_hint = self._font_small.render("PRESS  Q  TO  QUIT", True,
                                            (180, 180, 180))
        screen.blit(quit_hint, quit_hint.get_rect(centerx=cx, centery=405))
