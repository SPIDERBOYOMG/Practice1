"""
hud.py
======
Heads-Up Display renderer for PIXEL RACER – TSIS-3 Edition.

Panels
------
Top-left   : SCORE and road SPEED + enemy tier bar
Top-right  : coin count + weighted VALUE + last-pickup badge
Bottom-left: distance meter (driven / total)
Centre HUD : active power-up name + countdown ring
Centre msg : DANGER! flash / SHIELD flash / oil-slow warning
"""

import math
import pygame
import settings as S


class HUD:
    def __init__(self):
        try:
            self._font_big    = pygame.font.SysFont("monospace", 20, bold=True)
            self._font_med    = pygame.font.SysFont("monospace", 16, bold=True)
            self._font_small  = pygame.font.SysFont("monospace", 13, bold=True)
            self._font_tiny   = pygame.font.SysFont("monospace", 11, bold=False)
            self._font_huge   = pygame.font.SysFont("monospace", 48, bold=True)
            self._font_danger = pygame.font.SysFont("monospace", 26, bold=True)
        except Exception:
            self._font_big    = pygame.font.Font(None, 24)
            self._font_med    = pygame.font.Font(None, 20)
            self._font_small  = pygame.font.Font(None, 16)
            self._font_tiny   = pygame.font.Font(None, 14)
            self._font_huge   = pygame.font.Font(None, 54)
            self._font_danger = pygame.font.Font(None, 30)

        self._panel_l = self._panel(170, 66)
        self._panel_r = self._panel(155, 66)
        self._panel_b = self._panel(200, 34)

    @staticmethod
    def _panel(w, h):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 155))
        return s

    # ── Main draw ──────────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface,
             score: int, speed: float,
             coins_count: int, coin_value: int,
             last_coin_type,
             danger_flash: int, enemy_extra: float,
             distance: float,
             active_powerup=None, powerup_timer: float = 0.0,
             shield_active: bool = False,
             oil_slowed: bool = False) -> None:

        m = S.HUD_MARGIN

        # ── Left panel ────────────────────────────────────────────────────
        screen.blit(self._panel_l, (m, m))
        screen.blit(self._font_big.render(f"SCORE {score:06d}", True, S.COL_HUD_TEXT),
                    (m + 4, m + 4))
        screen.blit(self._font_small.render(f"SPEED  {speed:.1f}", True, S.COL_SCORE_TEXT),
                    (m + 4, m + 30))
        tier      = self._tier_label(enemy_extra)
        tier_col  = self._tier_color(enemy_extra)
        screen.blit(self._font_small.render(tier, True, tier_col),
                    (m + 4, m + 46))

        # ── Right panel ───────────────────────────────────────────────────
        px = S.WIN_W - 155 - m
        screen.blit(self._panel_r, (px, m))
        screen.blit(self._font_small.render("COINS", True, S.COL_SCORE_TEXT),
                    (px + 4, m + 2))
        screen.blit(self._font_big.render(f"x{coins_count:03d}", True, S.COL_COIN_TEXT),
                    (px + 4, m + 16))
        val_col = last_coin_type["label_color"] if last_coin_type else S.COL_SCORE_TEXT
        screen.blit(self._font_small.render(f"PTS {coin_value:04d}", True, val_col),
                    (px + 4, m + 42))
        if last_coin_type:
            badge = self._font_small.render(
                f"▶ {last_coin_type['name'].upper()}", True, last_coin_type["label_color"])
            screen.blit(badge, (px + 72, m + 42))

        # ── Bottom distance bar ───────────────────────────────────────────
        bx = S.WIN_W // 2 - 100
        screen.blit(self._panel_b, (bx, S.WIN_H - 42))
        frac = min(1.0, distance / S.RACE_DISTANCE_M)
        bar_w = int(180 * frac)
        pygame.draw.rect(screen, (40, 40, 60), (bx + 8, S.WIN_H - 30, 184, 12), border_radius=4)
        if bar_w > 0:
            bar_col = (80, 220, 100) if frac < 0.9 else (255, 220, 40)
            pygame.draw.rect(screen, bar_col, (bx + 8, S.WIN_H - 30, bar_w, 12), border_radius=4)
        dist_txt = self._font_tiny.render(
            f"{distance:.0f} m / {S.RACE_DISTANCE_M} m", True, S.COL_SCORE_TEXT)
        screen.blit(dist_txt, dist_txt.get_rect(centerx=S.WIN_W // 2, centery=S.WIN_H - 14))

        # ── Active power-up display ───────────────────────────────────────
        if active_powerup:
            self._draw_powerup_hud(screen, active_powerup, powerup_timer)

        # ── Shield indicator ──────────────────────────────────────────────
        if shield_active:
            s_txt = self._font_med.render("🛡 SHIELD ACTIVE", True, (100, 180, 255))
            screen.blit(s_txt, s_txt.get_rect(centerx=S.WIN_W // 2, centery=S.WIN_H - 60))

        # ── Oil slow indicator ────────────────────────────────────────────
        if oil_slowed:
            o_txt = self._font_med.render("⚠ OIL SPILL – SLOWED", True, (160, 100, 255))
            screen.blit(o_txt, o_txt.get_rect(centerx=S.WIN_W // 2, centery=S.WIN_H - 78))

        # ── Danger flash ──────────────────────────────────────────────────
        if danger_flash > 0:
            self._draw_danger(screen, danger_flash)

    # ── Power-up HUD panel ─────────────────────────────────────────────────────

    def _draw_powerup_hud(self, screen, pu_type: dict, timer: float):
        cx = S.WIN_W // 2
        y  = 90
        # Background pill
        pill = pygame.Surface((160, 28), pygame.SRCALPHA)
        pill.fill((0, 0, 0, 160))
        screen.blit(pill, (cx - 80, y))
        pygame.draw.rect(screen, pu_type["color"], (cx - 80, y, 160, 28), 2, border_radius=6)

        label = self._font_med.render(
            f"{pu_type['label']}  {timer:.1f}s" if timer else pu_type["label"],
            True, pu_type["color"])
        screen.blit(label, label.get_rect(centerx=cx, centery=y + 14))

        # Countdown arc (only for timed powerups)
        if timer and pu_type.get("duration"):
            frac  = max(0, timer / pu_type["duration"])
            r     = 12
            arc_x = cx + 68
            arc_y = y + 14
            pygame.draw.circle(screen, (40, 40, 60), (arc_x, arc_y), r)
            end_angle = math.radians(90 - 360 * frac)
            if frac > 0:
                pts = [(arc_x, arc_y)]
                steps = max(8, int(frac * 32))
                for i in range(steps + 1):
                    a = math.radians(90) - (2 * math.pi * frac * i / steps)
                    pts.append((arc_x + int(r * math.cos(a)),
                                arc_y - int(r * math.sin(a))))
                if len(pts) >= 3:
                    pygame.draw.polygon(screen, pu_type["color"] + (200,), pts)

    # ── Danger banner ──────────────────────────────────────────────────────────

    def _draw_danger(self, screen, timer: int):
        bright = (timer // 8) % 2 == 0
        colour = S.COL_DANGER if bright else S.COL_DANGER_DIM
        alpha  = min(255, timer * 5)
        cx     = S.WIN_W // 2
        line1  = self._font_danger.render("⚠  DANGER!  ⚠", True, colour)
        line2  = self._font_med.render("ENEMY  SPEED  UP",  True, S.COL_WHITE)
        line1.set_alpha(alpha)
        line2.set_alpha(alpha)
        screen.blit(line1, line1.get_rect(centerx=cx, centery=130))
        screen.blit(line2, line2.get_rect(centerx=cx, centery=162))

    # ── Tier helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _tier_label(extra: float) -> str:
        if extra <= S.ENEMY_SPEED_EXTRA:
            return "ENEMY ░░░░"
        boosts = round((extra - S.ENEMY_SPEED_EXTRA) / S.ENEMY_BOOST_AMOUNT)
        filled = min(boosts, 4)
        return f"ENEMY {'█' * filled}{'░' * (4 - filled)}"

    @staticmethod
    def _tier_color(extra: float) -> tuple:
        ratio = (extra - S.ENEMY_SPEED_EXTRA) / max(
            1, S.ENEMY_SPEED_EXTRA_MAX - S.ENEMY_SPEED_EXTRA)
        ratio = max(0.0, min(1.0, ratio))
        return (int(255 * ratio), int(255 * (1 - ratio)), 0)
