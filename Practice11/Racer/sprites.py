"""
sprites.py
==========
All pygame.Sprite subclasses for PIXEL RACER.

Classes
-------
PlayerCar  – player-controlled car; moves left/right, clamped to road.
EnemyCar   – AI obstacle car; speed = road_scroll + enemy_extra_speed.
Coin       – weighted collectible; drawn procedurally from COIN_TYPES data.
Explosion  – one-shot 4-frame explosion animation.
"""

import math
import random
import pygame
import settings as S


# ════════════════════════════════════════════════════════════════════════════
#  PlayerCar
# ════════════════════════════════════════════════════════════════════════════
class PlayerCar(pygame.sprite.Sprite):
    """
    The player's car.
    Reads keyboard state every frame and moves horizontally.
    Clamped so it can never leave the asphalt area.
    """

    def __init__(self, image: pygame.Surface):
        super().__init__()
        # Scale 2× for a chunky retro pixel look
        self.image = pygame.transform.scale(
            image, (image.get_width() * 2, image.get_height() * 2)
        )
        self.rect = self.image.get_rect()
        # Start in the bottom-centre of the screen
        self.rect.centerx = S.PLAYER_START_X
        self.rect.bottom   = S.PLAYER_START_Y

    def update(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Shift the car left/right and keep it within road boundaries."""
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= S.PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += S.PLAYER_SPEED

        # Clamp to road edges (kerb-to-kerb)
        self.rect.left  = max(self.rect.left,  S.ROAD_LEFT)
        self.rect.right = min(self.rect.right, S.ROAD_RIGHT)


# ════════════════════════════════════════════════════════════════════════════
#  EnemyCar
# ════════════════════════════════════════════════════════════════════════════
class EnemyCar(pygame.sprite.Sprite):
    """
    An oncoming obstacle car.

    Speed  =  road_scroll_speed  +  enemy_extra_speed
    enemy_extra_speed is passed in each frame from the Game object so it
    can be raised dynamically by the enemy-boost system.

    A random colour tint is applied to the sprite for visual variety
    without requiring additional art assets.
    """

    # Colour tints multiplied onto the base enemy sprite
    TINTS = [
        (255, 255, 255),   # original red (no tint)
        (255, 200, 100),   # orange
        (180,  80, 200),   # purple
        (100, 200, 100),   # green
        (255, 255,  80),   # yellow
    ]

    def __init__(self, image: pygame.Surface, scroll_speed: float,
                 enemy_extra: float):
        """
        Parameters
        ----------
        image        : base enemy-car surface
        scroll_speed : current road scroll speed (px/frame)
        enemy_extra  : current enemy extra speed (px/frame); stored so
                       update() can recalculate speed each frame
        """
        super().__init__()

        # ── Apply random colour tint for variety ──────────────────────────
        tint   = random.choice(self.TINTS)
        tinted = image.copy()
        # BLEND_RGBA_MULT multiplies each channel; alpha must be 255 (opaque)
        tinted.fill(tint + (255,), special_flags=pygame.BLEND_RGBA_MULT)

        # Scale 2× to match the player car size
        self.image = pygame.transform.scale(
            tinted, (tinted.get_width() * 2, tinted.get_height() * 2)
        )
        self.rect = self.image.get_rect()

        # ── Spawn position ────────────────────────────────────────────────
        self.rect.centerx = random.choice(S.LANES)
        self.rect.bottom  = 0    # just above the visible screen

        # ── Speed state ───────────────────────────────────────────────────
        # enemy_extra is kept as a reference value; update() reads the
        # latest value passed in from Game so all enemies accelerate together.
        self._extra = enemy_extra
        self.speed  = scroll_speed + enemy_extra

    def update(self, scroll_speed: float, enemy_extra: float = None) -> None:
        """
        Scroll the car downward each frame.
        Accepts the latest enemy_extra so newly-boosted speed is applied
        immediately to every car on screen (not just newly spawned ones).
        Removes itself when it scrolls fully past the bottom edge.
        """
        if enemy_extra is not None:
            self._extra = enemy_extra

        # Recalculate speed with latest values
        self.speed   = scroll_speed + self._extra
        self.rect.y += int(self.speed)

        # Kill this sprite once it is fully off the bottom of the screen
        if self.rect.top > S.WIN_H:
            self.kill()


# ════════════════════════════════════════════════════════════════════════════
#  Coin
# ════════════════════════════════════════════════════════════════════════════
class Coin(pygame.sprite.Sprite):
    """
    A collectible coin drawn procedurally based on its type definition.

    Type is chosen via weighted random selection at spawn time.
    Each type has a different:
      • visual appearance  (colour, size)
      • point value        (awarded when collected)
      • spawn probability  (weight in the weighted draw)

    The coin animates with a smooth sin-wave scale-bob each frame.

    Public attributes
    -----------------
    value     : int   – score points this coin is worth
    coin_type : dict  – the COIN_TYPES entry this instance was built from
    """

    # Base coin radius in pixels before radius_factor scaling
    BASE_RADIUS = 10

    def __init__(self, coin_type: dict, scroll_speed: float):
        """
        Parameters
        ----------
        coin_type    : one entry from settings.COIN_TYPES
        scroll_speed : current road scroll speed (px/frame)
        """
        super().__init__()

        # Store type metadata so callers can read .value and .coin_type
        self.coin_type = coin_type
        self.value     = coin_type["value"]

        # Coin's scroll speed is a fraction of the road's speed
        self.speed = scroll_speed * S.COIN_SPEED_FACTOR

        # ── Spawn at a random lane, just above the screen ─────────────────
        self._lane_x = random.choice(S.LANES)

        # Animation oscillator: randomised start so coins bob out of phase
        self._anim_t = random.randint(0, 360)

        # Build the initial surface
        self.image, self.rect = self._build_image(1.0)
        self.rect.centerx = self._lane_x
        self.rect.bottom  = 0

    # ── Surface builder ───────────────────────────────────────────────────────

    def _build_image(self, scale: float) -> tuple[pygame.Surface, pygame.Rect]:
        """
        Draw the coin as a pixel-art circle with highlight and value label.

        Parameters
        ----------
        scale : float — extra scale factor applied on top of radius_factor

        Returns
        -------
        (surface, rect)  where rect is centred at the coin's current centre.
        """
        ct = self.coin_type
        r  = max(4, int(self.BASE_RADIUS * ct["radius_factor"] * scale))
        size = r * 2 + 6    # canvas with a small margin for the outline glow

        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))

        cx = cy = size // 2

        # ── Outer glow (for rare coins only) ─────────────────────────────
        if ct["name"] in ("gold", "gem"):
            glow_col = ct["color"] + (60,)   # semi-transparent
            pygame.draw.circle(surf, glow_col, (cx, cy), r + 3)

        # ── Outline / shadow ──────────────────────────────────────────────
        pygame.draw.circle(surf, ct["outline"] + (255,), (cx, cy), r)

        # ── Main body ─────────────────────────────────────────────────────
        pygame.draw.circle(surf, ct["color"] + (255,), (cx, cy), r - 1)

        # ── Inner ring (slightly darker, gives depth) ─────────────────────
        inner_r = max(2, r - 3)
        dark = tuple(max(0, c - 40) for c in ct["color"])
        pygame.draw.circle(surf, dark + (180,), (cx, cy), inner_r)

        # ── Highlight spot (top-left) ─────────────────────────────────────
        hl_r = max(2, r // 3)
        pygame.draw.circle(surf, ct["highlight"] + (220,),
                           (cx - r // 3, cy - r // 3), hl_r)

        # ── Pixel-art value label (e.g. "×5") ────────────────────────────
        # Only draw if radius is large enough to fit text legibly
        if r >= 9:
            try:
                font = pygame.font.SysFont("monospace", max(8, r - 2), bold=True)
                label = font.render(f"×{self.value}", True,
                                    ct["highlight"] + (255,))
                lr = label.get_rect(center=(cx, cy + 1))
                surf.blit(label, lr)
            except Exception:
                pass   # font unavailable — skip label gracefully

        return surf, surf.get_rect()

    # ── Sprite update ─────────────────────────────────────────────────────────

    def update(self, scroll_speed: float, enemy_extra: float = None) -> None:
        """
        Scroll downward and animate the bob effect each frame.
        enemy_extra is accepted but ignored (coins don't react to enemy speed).
        Removes itself when off-screen.
        """
        # Recalculate scroll speed in case the game sped up
        self.speed = scroll_speed * S.COIN_SPEED_FACTOR
        self.rect.y += int(self.speed)

        # ── Sin-wave scale bob (90% – 112% of base size) ──────────────────
        self._anim_t = (self._anim_t + 4) % 360
        scale = 1.0 + 0.11 * math.sin(math.radians(self._anim_t))

        # Rebuild image at new scale, keeping the same centre position
        cx, cy = self.rect.centerx, self.rect.centery
        self.image, self.rect = self._build_image(scale)
        self.rect.center = (cx, cy)

        # Remove once fully scrolled past the bottom of the screen
        if self.rect.top > S.WIN_H:
            self.kill()


# ════════════════════════════════════════════════════════════════════════════
#  Helper: weighted random coin type picker
# ════════════════════════════════════════════════════════════════════════════
def pick_coin_type() -> dict:
    """
    Select a coin type from settings.COIN_TYPES using weighted random sampling.

    Higher-weight types appear more often.  The algorithm:
      1. Sum all weights.
      2. Pick a random float in [0, total_weight).
      3. Walk the list subtracting each weight until the remainder ≤ 0.

    Returns one entry from COIN_TYPES.
    """
    total  = sum(ct["weight"] for ct in S.COIN_TYPES)
    roll   = random.uniform(0, total)
    for ct in S.COIN_TYPES:
        roll -= ct["weight"]
        if roll <= 0:
            return ct
    return S.COIN_TYPES[-1]   # fallback (should never be reached)


# ════════════════════════════════════════════════════════════════════════════
#  Explosion
# ════════════════════════════════════════════════════════════════════════════
class Explosion(pygame.sprite.Sprite):
    """
    A 4-frame pixel explosion animation.
    Plays once then removes itself from all sprite groups.
    """

    def __init__(self, frames: list[pygame.Surface], center: tuple[int, int]):
        super().__init__()
        # Scale each frame 2× to match the pixel-art car scale
        self._frames = [
            pygame.transform.scale(f, (f.get_width() * 2, f.get_height() * 2))
            for f in frames
        ]
        self._frame_index = 0   # index into self._frames
        self._frame_timer = 0   # counts display frames until next sprite frame

        self.image = self._frames[0]
        self.rect  = self.image.get_rect(center=center)

    def update(self, *_args) -> None:
        """Advance to the next frame; kill self when the animation ends."""
        self._frame_timer += 1
        if self._frame_timer >= S.EXPLOSION_FRAME_DUR:
            self._frame_timer  = 0
            self._frame_index += 1
            if self._frame_index >= len(self._frames):
                self.kill()   # animation complete — remove from all groups
                return
            # Update surface but keep the same screen position
            cx, cy     = self.rect.centerx, self.rect.centery
            self.image = self._frames[self._frame_index]
            self.rect  = self.image.get_rect(center=(cx, cy))
