"""
sprites.py
==========
All pygame.Sprite subclasses for PIXEL RACER – TSIS-3 Edition.

Classes (Practice 10-11 unchanged)
--------------------------------------
PlayerCar  – player car; horizontal movement; supports tint + oil-slow
EnemyCar   – AI obstacle; speed = road_scroll + enemy_extra
Coin       – weighted collectible (bronze/silver/gold/gem)
Explosion  – 4-frame animation

New for TSIS-3
--------------
Obstacle   – pothole / oil_spill / barrier drawn procedurally
PowerUp    – nitro / shield / repair collectible
NitroStrip – temporary road event that boosts scroll speed
"""

import math
import random
import pygame
import settings as S


# ════════════════════════════════════════════════════════════════════════════
#  PlayerCar
# ════════════════════════════════════════════════════════════════════════════
class PlayerCar(pygame.sprite.Sprite):
    def __init__(self, image: pygame.Surface, tint: tuple = (255, 255, 255)):
        super().__init__()
        tinted = image.copy()
        tinted.fill(tint[:3] + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        self.image = pygame.transform.scale(
            tinted, (image.get_width() * 2, image.get_height() * 2)
        )
        self.rect = self.image.get_rect()
        self.rect.centerx = S.PLAYER_START_X
        self.rect.bottom  = S.PLAYER_START_Y

        self._oil_slow_timer = 0.0   # seconds remaining of oil slow effect
        self._shield_active  = False

    @property
    def shielded(self): return self._shield_active

    def activate_shield(self):  self._shield_active = True
    def consume_shield(self):   self._shield_active = False

    def apply_oil(self):
        self._oil_slow_timer = S.OIL_SLOW_DURATION

    def update(self, keys, dt: float, speed_override: float | None = None):
        # Oil slow
        move_speed = S.PLAYER_SPEED
        if self._oil_slow_timer > 0:
            self._oil_slow_timer = max(0.0, self._oil_slow_timer - dt)
            move_speed = int(S.PLAYER_SPEED * S.OIL_SLOW_FACTOR)

        if speed_override is not None:
            move_speed = speed_override

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= move_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += move_speed

        self.rect.left  = max(self.rect.left,  S.ROAD_LEFT)
        self.rect.right = min(self.rect.right, S.ROAD_RIGHT)

    @property
    def oil_slowed(self): return self._oil_slow_timer > 0


# ════════════════════════════════════════════════════════════════════════════
#  EnemyCar
# ════════════════════════════════════════════════════════════════════════════
class EnemyCar(pygame.sprite.Sprite):
    TINTS = [
        (255, 255, 255), (255, 200, 100),
        (180,  80, 200), (100, 200, 100), (255, 255, 80),
    ]

    def __init__(self, image: pygame.Surface, scroll_speed: float, enemy_extra: float):
        super().__init__()
        tint   = random.choice(self.TINTS)
        tinted = image.copy()
        tinted.fill(tint[:3] + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        self.image = pygame.transform.scale(
            tinted, (tinted.get_width() * 2, tinted.get_height() * 2)
        )
        self.rect = self.image.get_rect()
        self.rect.centerx = random.choice(S.LANES)
        self.rect.bottom  = -10
        self._extra = enemy_extra
        self.speed  = scroll_speed + enemy_extra

    def update(self, scroll_speed: float, enemy_extra: float = None, **_):
        if enemy_extra is not None:
            self._extra = enemy_extra
        self.speed   = scroll_speed + self._extra
        self.rect.y += int(self.speed)
        if self.rect.top > S.WIN_H:
            self.kill()


# ════════════════════════════════════════════════════════════════════════════
#  Coin
# ════════════════════════════════════════════════════════════════════════════
class Coin(pygame.sprite.Sprite):
    BASE_RADIUS = 10

    def __init__(self, coin_type: dict, scroll_speed: float):
        super().__init__()
        self.coin_type = coin_type
        self.value     = coin_type["value"]
        self.speed     = scroll_speed * S.COIN_SPEED_FACTOR
        self._lane_x   = random.choice(S.LANES)
        self._anim_t   = random.randint(0, 360)
        self.image, self.rect = self._build_image(1.0)
        self.rect.centerx = self._lane_x
        self.rect.bottom  = 0

    def _build_image(self, scale: float):
        ct = self.coin_type
        r  = max(4, int(self.BASE_RADIUS * ct["radius_factor"] * scale))
        size = r * 2 + 6
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        cx = cy = size // 2
        if ct["name"] in ("gold", "gem"):
            pygame.draw.circle(surf, ct["color"] + (60,), (cx, cy), r + 3)
        pygame.draw.circle(surf, ct["outline"] + (255,), (cx, cy), r)
        pygame.draw.circle(surf, ct["color"]   + (255,), (cx, cy), r - 1)
        inner_r = max(2, r - 3)
        dark = tuple(max(0, c - 40) for c in ct["color"])
        pygame.draw.circle(surf, dark + (180,), (cx, cy), inner_r)
        hl_r = max(2, r // 3)
        pygame.draw.circle(surf, ct["highlight"] + (220,),
                           (cx - r // 3, cy - r // 3), hl_r)
        if r >= 9:
            try:
                font  = pygame.font.SysFont("monospace", max(8, r - 2), bold=True)
                label = font.render(f"×{self.value}", True, ct["highlight"] + (255,))
                surf.blit(label, label.get_rect(center=(cx, cy + 1)))
            except Exception:
                pass
        return surf, surf.get_rect()

    def update(self, scroll_speed: float, **_):
        self.speed  = scroll_speed * S.COIN_SPEED_FACTOR
        self.rect.y += int(self.speed)
        self._anim_t = (self._anim_t + 4) % 360
        scale = 1.0 + 0.11 * math.sin(math.radians(self._anim_t))
        cx, cy = self.rect.centerx, self.rect.centery
        self.image, self.rect = self._build_image(scale)
        self.rect.center = (cx, cy)
        if self.rect.top > S.WIN_H:
            self.kill()


def pick_coin_type() -> dict:
    total = sum(ct["weight"] for ct in S.COIN_TYPES)
    roll  = random.uniform(0, total)
    for ct in S.COIN_TYPES:
        roll -= ct["weight"]
        if roll <= 0:
            return ct
    return S.COIN_TYPES[-1]


# ════════════════════════════════════════════════════════════════════════════
#  Obstacle  (NEW)
# ════════════════════════════════════════════════════════════════════════════
class Obstacle(pygame.sprite.Sprite):
    """
    Road hazard: pothole / oil_spill / barrier.
    Drawn procedurally from OBSTACLE_TYPES table.
    """

    def __init__(self, obs_type: dict, scroll_speed: float):
        super().__init__()
        self.obs_type = obs_type
        self.speed    = scroll_speed * S.OBSTACLE_SPEED_FACTOR
        self._anim_t  = 0

        w, h = obs_type["w"], obs_type["h"]
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        name = obs_type["name"]
        if name == "pothole":
            pygame.draw.ellipse(surf, obs_type["color"], (0, 0, w, h))
            pygame.draw.ellipse(surf, obs_type["border"], (0, 0, w, h), 2)
            # Crack lines for detail
            mid = (w // 2, h // 2)
            pygame.draw.line(surf, (40, 40, 45), mid, (w - 4, 4), 1)
            pygame.draw.line(surf, (40, 40, 45), mid, (4, h - 4), 1)

        elif name == "oil_spill":
            # Irregular blob
            pygame.draw.ellipse(surf, obs_type["color"], (0, 4, w, h - 4))
            pygame.draw.ellipse(surf, obs_type["border"], (0, 4, w, h - 4), 2)
            # Iridescent shimmer dots
            shimmer = [(80, 80, 160, 120), (100, 60, 200, 100)]
            for i, sc in enumerate(shimmer):
                pygame.draw.circle(surf, sc, (w // 3 + i * 8, h // 2), 4)

        elif name == "barrier":
            pygame.draw.rect(surf, obs_type["color"], (0, 0, w, h), border_radius=3)
            pygame.draw.rect(surf, obs_type["border"], (0, 0, w, h), 2, border_radius=3)
            # Diagonal stripes
            for i in range(0, w, 8):
                pygame.draw.line(surf, (200, 80, 0), (i, 0), (i + h, h), 2)

        self.image = surf
        self.rect  = surf.get_rect()
        self.rect.centerx = random.choice(S.LANES)
        self.rect.bottom  = -10

    def update(self, scroll_speed: float, **_):
        self.speed  = scroll_speed * S.OBSTACLE_SPEED_FACTOR
        self.rect.y += int(self.speed)

        # Oil spill: gentle colour pulse
        if self.obs_type["name"] == "oil_spill":
            self._anim_t = (self._anim_t + 3) % 360

        if self.rect.top > S.WIN_H:
            self.kill()


def pick_obstacle_type() -> dict:
    return random.choice(S.OBSTACLE_TYPES)


# ════════════════════════════════════════════════════════════════════════════
#  PowerUp  (NEW)
# ════════════════════════════════════════════════════════════════════════════
class PowerUp(pygame.sprite.Sprite):
    """
    Collectible power-up (nitro / shield / repair).
    Disappears after POWERUP_LIFETIME_S seconds if not collected.
    """

    SIZE = 26

    def __init__(self, pu_type: dict, scroll_speed: float):
        super().__init__()
        self.pu_type      = pu_type
        self.speed        = scroll_speed * S.POWERUP_SPEED_FACTOR
        self._lifetime    = S.POWERUP_LIFETIME_S  # seconds
        self._anim_t      = 0
        self._blink_start = S.POWERUP_LIFETIME_S * 0.4  # blink in last 40%

        self.image = self._build(1.0)
        self.rect  = self.image.get_rect()
        self.rect.centerx = random.choice(S.LANES)
        self.rect.bottom  = -10

    def _build(self, scale: float) -> pygame.Surface:
        sz   = max(10, int(self.SIZE * scale))
        surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
        cx = cy = sz // 2
        r  = sz // 2 - 2

        # Background circle
        pygame.draw.circle(surf, self.pu_type["color"] + (220,), (cx, cy), r)
        pygame.draw.circle(surf, (255, 255, 255, 80), (cx, cy), r, 2)

        # Symbol via tiny font
        try:
            font  = pygame.font.SysFont("segoe ui emoji", max(10, sz - 8), bold=True)
            label = font.render(self.pu_type.get("symbol", "?"), True,
                                self.pu_type["icon_col"] + (255,))
            surf.blit(label, label.get_rect(center=(cx, cy)))
        except Exception:
            # Fallback: initials
            font  = pygame.font.SysFont("monospace", max(8, sz // 2), bold=True)
            label = font.render(self.pu_type["name"][0].upper(), True, (255, 255, 255))
            surf.blit(label, label.get_rect(center=(cx, cy)))

        return surf

    def update(self, scroll_speed: float, dt: float = 1 / 60, **_):
        self.speed     = scroll_speed * S.POWERUP_SPEED_FACTOR
        self.rect.y   += int(self.speed)
        self._lifetime -= dt
        if self._lifetime <= 0 or self.rect.top > S.WIN_H:
            self.kill()
            return

        # Bob + optional blink
        self._anim_t = (self._anim_t + 5) % 360
        scale = 1.0 + 0.12 * math.sin(math.radians(self._anim_t))
        if self._lifetime < self._blink_start:
            blink_hz = 6
            visible  = int(self._lifetime * blink_hz * 2) % 2 == 0
            if not visible:
                self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
                return

        cx, cy = self.rect.centerx, self.rect.centery
        self.image = self._build(scale)
        self.rect  = self.image.get_rect(center=(cx, cy))


def pick_powerup_type() -> dict:
    return random.choice(S.POWERUP_TYPES)


# ════════════════════════════════════════════════════════════════════════════
#  NitroStrip  (NEW – road event)
# ════════════════════════════════════════════════════════════════════════════
class NitroStrip(pygame.sprite.Sprite):
    """
    A glowing speed-boost strip that spans the full road width.
    Driving over it temporarily raises scroll_speed.
    """

    H = 18

    def __init__(self, scroll_speed: float):
        super().__init__()
        w   = S.ROAD_RIGHT - S.ROAD_LEFT
        surf = pygame.Surface((w, self.H), pygame.SRCALPHA)

        # Gradient-ish yellow strip
        for y in range(self.H):
            alpha = int(200 * (1 - abs(y - self.H // 2) / (self.H // 2 + 1)))
            pygame.draw.line(surf, (255, 230, 0, alpha), (0, y), (w, y))

        # Arrow chevrons
        arrow_col = (255, 160, 0, 255)
        step = 28
        for i in range(0, w, step):
            pts = [(i + 6, 2), (i + 14, self.H // 2), (i + 6, self.H - 2)]
            if all(0 <= p[0] <= w for p in pts):
                pygame.draw.lines(surf, arrow_col, False, pts, 2)

        self.image = surf
        self.rect  = surf.get_rect()
        self.rect.left   = S.ROAD_LEFT
        self.rect.bottom = -10
        self.speed        = scroll_speed

    def update(self, scroll_speed: float, **_):
        self.speed  = scroll_speed
        self.rect.y += int(self.speed)
        if self.rect.top > S.WIN_H:
            self.kill()


# ════════════════════════════════════════════════════════════════════════════
#  Explosion  (unchanged from Practice 10-11)
# ════════════════════════════════════════════════════════════════════════════
class Explosion(pygame.sprite.Sprite):
    def __init__(self, frames: list[pygame.Surface], center: tuple[int, int]):
        super().__init__()
        self._frames = [
            pygame.transform.scale(f, (f.get_width() * 2, f.get_height() * 2))
            for f in frames
        ]
        self._frame_index = 0
        self._frame_timer = 0
        self.image = self._frames[0]
        self.rect  = self.image.get_rect(center=center)

    def update(self, *_args, **_kw):
        self._frame_timer += 1
        if self._frame_timer >= S.EXPLOSION_FRAME_DUR:
            self._frame_timer  = 0
            self._frame_index += 1
            if self._frame_index >= len(self._frames):
                self.kill()
                return
            cx, cy     = self.rect.centerx, self.rect.centery
            self.image = self._frames[self._frame_index]
            self.rect  = self.image.get_rect(center=(cx, cy))
