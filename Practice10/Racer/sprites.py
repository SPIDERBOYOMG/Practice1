"""
sprites.py
==========
All pygame.Sprite subclasses for the Racer game:
  - PlayerCar  : the player-controlled car
  - EnemyCar   : AI obstacle cars coming from the top
  - Coin       : collectible coin that spawns randomly on the road
  - Explosion  : short frame-by-frame explosion animation on collision
"""

import random
import pygame
import settings as S


# ════════════════════════════════════════════════════════════════════════════
#  PlayerCar
# ════════════════════════════════════════════════════════════════════════════
class PlayerCar(pygame.sprite.Sprite):
    """
    The player's car, moved left/right with arrow keys or A/D.
    Stays within the road boundaries defined in settings.
    """

    def __init__(self, image: pygame.Surface):
        super().__init__()
        # Scale the sprite up 2× for a chunky retro look
        self.image = pygame.transform.scale(image, (image.get_width() * 2,
                                                     image.get_height() * 2))
        self.rect  = self.image.get_rect()
        # Place the car at the bottom-centre of the screen
        self.rect.centerx = S.PLAYER_START_X
        self.rect.bottom   = S.PLAYER_START_Y

    def update(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Move left/right based on pressed keys; clamp to road edges."""
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= S.PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += S.PLAYER_SPEED

        # Clamp: car must stay on the road (left kerb → right kerb)
        self.rect.left  = max(self.rect.left,  S.ROAD_LEFT)
        self.rect.right = min(self.rect.right, S.ROAD_RIGHT)


# ════════════════════════════════════════════════════════════════════════════
#  EnemyCar
# ════════════════════════════════════════════════════════════════════════════
class EnemyCar(pygame.sprite.Sprite):
    """
    An oncoming enemy car that spawns at the top of the screen in a
    random lane and scrolls downward.  It is also tinted a random hue
    to add visual variety without needing extra art assets.
    """

    # Hue tints applied to the enemy sprite for variety
    TINTS = [
        (255, 255, 255),   # original red
        (255, 200, 100),   # orange
        (180,  80, 200),   # purple
        (100, 200, 100),   # green
        (255, 255,  80),   # yellow
    ]

    def __init__(self, image: pygame.Surface, scroll_speed: float):
        super().__init__()

        # Apply a random colour tint for variety
        tint = random.choice(self.TINTS)
        tinted = image.copy()
        tinted.fill(tint + (255,), special_flags=pygame.BLEND_RGBA_MULT)

        # Scale up 2× to match the player car
        self.image = pygame.transform.scale(tinted, (tinted.get_width() * 2,
                                                      tinted.get_height() * 2))
        self.rect  = self.image.get_rect()

        # Pick a random lane centre for the starting X position
        lane_cx = random.choice(S.LANES)
        self.rect.centerx = lane_cx
        self.rect.bottom  = 0   # spawn just above the visible area

        # Move faster than the road scroll to create "approaching" feel
        self.speed = scroll_speed + S.ENEMY_SPEED_EXTRA

    def update(self, scroll_speed: float) -> None:
        """Scroll downward.  Remove self when fully off the bottom."""
        self.speed = scroll_speed + S.ENEMY_SPEED_EXTRA
        self.rect.y += int(self.speed)

        if self.rect.top > S.WIN_H:
            self.kill()   # pygame removes this sprite from all groups


# ════════════════════════════════════════════════════════════════════════════
#  Coin
# ════════════════════════════════════════════════════════════════════════════
class Coin(pygame.sprite.Sprite):
    """
    A gold coin that appears at a random lane and scrolls down the road.
    Collecting it increments the player's coin counter.
    The coin animates with a simple scale-pulse (bob) effect each frame.
    """

    def __init__(self, image: pygame.Surface, scroll_speed: float):
        super().__init__()
        self._base_image = image      # keep original for scaling animation
        self.image  = image.copy()
        self.rect   = self.image.get_rect()
        self.speed  = scroll_speed * S.COIN_SPEED_FACTOR

        # Pick a random lane and place just above the visible screen
        lane_cx = random.choice(S.LANES)
        self.rect.centerx = lane_cx
        self.rect.bottom  = 0

        # Animation state: oscillates 0→360 for the scale bob
        self._anim_t = random.randint(0, 360)

    def update(self, scroll_speed: float) -> None:
        """Scroll down and animate. Remove when off-screen."""
        self.speed = scroll_speed * S.COIN_SPEED_FACTOR
        self.rect.y += int(self.speed)

        # Simple bob: scale the image between 90% and 110% of original
        import math
        self._anim_t = (self._anim_t + 4) % 360
        scale_factor = 1.0 + 0.1 * math.sin(math.radians(self._anim_t))
        w = int(self._base_image.get_width()  * scale_factor * 2)
        h = int(self._base_image.get_height() * scale_factor * 2)
        cx, cy = self.rect.centerx, self.rect.centery
        self.image = pygame.transform.scale(self._base_image, (w, h))
        self.rect  = self.image.get_rect(center=(cx, cy))

        if self.rect.top > S.WIN_H:
            self.kill()


# ════════════════════════════════════════════════════════════════════════════
#  Explosion
# ════════════════════════════════════════════════════════════════════════════
class Explosion(pygame.sprite.Sprite):
    """
    A 4-frame explosion animation that plays once then removes itself.
    Centred at the given position.
    """

    def __init__(self, frames: list[pygame.Surface], center: tuple[int, int]):
        super().__init__()
        # Scale each frame 2× for the pixel-art aesthetic
        self._frames = [
            pygame.transform.scale(f, (f.get_width() * 2, f.get_height() * 2))
            for f in frames
        ]
        self._frame_index  = 0      # which sprite frame is showing
        self._frame_timer  = 0      # countdown until next frame

        self.image = self._frames[0]
        self.rect  = self.image.get_rect(center=center)

    def update(self, *_args) -> None:
        """Advance the frame sequence; kill self when animation ends."""
        self._frame_timer += 1
        if self._frame_timer >= S.EXPLOSION_FRAME_DUR:
            self._frame_timer = 0
            self._frame_index += 1
            if self._frame_index >= len(self._frames):
                self.kill()   # animation finished
                return
            # Update image + keep same centre
            cx, cy = self.rect.centerx, self.rect.centery
            self.image = self._frames[self._frame_index]
            self.rect  = self.image.get_rect(center=(cx, cy))
