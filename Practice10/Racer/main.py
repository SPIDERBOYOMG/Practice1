"""
main.py  —  PIXEL RACER
========================
Top-down lane racer game built with Pygame.
Based on the CodersLegacy Pygame Tutorial (Parts 1–3) with extra features:
  ✓ Randomly appearing coins on the road
  ✓ Coin counter displayed in the top-right corner (HUD)
  ✓ Pixel / retro art style (1:1 upscaled sprites, chunky monospace font)
  ✓ Explosion animation on collision
  ✓ Increasing difficulty (speed ramps up over time)

Controls:
  ← / A   move left
  → / D   move right
  R       restart after Game Over
  Q/ESC   quit
"""

import sys
import random
import pygame

import settings as S
from sprites  import PlayerCar, EnemyCar, Coin, Explosion
from hud      import HUD


# ════════════════════════════════════════════════════════════════════════════
#  Asset loading helpers
# ════════════════════════════════════════════════════════════════════════════

def load_image(name: str) -> pygame.Surface:
    """
    Load a PNG from the assets folder.
    If the file is missing, run the asset generator first and retry.
    """
    path = S.asset(name)
    try:
        return pygame.image.load(path).convert_alpha()
    except FileNotFoundError:
        # Auto-generate assets on first run
        print(f"[INFO] Asset '{name}' not found – generating assets …")
        import generate_assets  # noqa: F401  (runs module-level code)
        return pygame.image.load(path).convert_alpha()


def load_explosion_frames() -> list[pygame.Surface]:
    """Load all 4 explosion frame PNGs into a list."""
    frames = []
    for i in range(4):
        frames.append(load_image(f"explosion_{i}.png"))
    return frames


# ════════════════════════════════════════════════════════════════════════════
#  Game class
# ════════════════════════════════════════════════════════════════════════════

class Game:
    """
    Encapsulates the entire game state and logic.
    Call game.run() to start the main loop.
    Calling game.reset() reinitialises everything for a fresh game.
    """

    def __init__(self):
        pygame.init()
        # Create the window; SCALED keeps integer pixel-perfect rendering
        self.screen = pygame.display.set_mode((S.WIN_W, S.WIN_H),
                                              pygame.SCALED)
        pygame.display.set_caption(S.TITLE)
        self.clock  = pygame.time.Clock()

        # Load all assets once (reused across resets)
        self._img_player    = load_image("player_car.png")
        self._img_enemy     = load_image("enemy_car.png")
        self._img_coin      = load_image("coin.png")
        self._img_road      = load_image("road_bg.png")
        self._explosion_frames = load_explosion_frames()

        # The HUD renderer
        self.hud = HUD(self._img_coin)

        self.reset()

    # ── Initialise / reset game state ────────────────────────────────────────
    def reset(self) -> None:
        """Set (or reset) all mutable game state for a fresh run."""

        # ── Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.enemies     = pygame.sprite.Group()
        self.coins       = pygame.sprite.Group()
        self.explosions  = pygame.sprite.Group()

        # ── Player
        self.player = PlayerCar(self._img_player)
        self.all_sprites.add(self.player)

        # ── Scrolling road: two tiles stacked so one is always on-screen
        # road_y_top tracks the top tile's current Y position
        self._road_h   = self._img_road.get_height()   # 600 px
        self._road_y   = 0    # top of first tile; second tile = road_y - road_h

        # ── Difficulty / pacing
        self.scroll_speed   = float(S.SCROLL_SPEED_INIT)
        self._enemy_timer   = 0         # frames since last enemy spawn
        self._enemy_delay   = S.ENEMY_SPAWN_DELAY

        # ── Score & collectibles
        self.score      = 0    # increases every frame the player is alive
        self.coins_collected = 0

        # ── State flags
        self.game_over  = False

    # ── Main event / input handling ───────────────────────────────────────────
    def _handle_events(self) -> None:
        """Process OS and keyboard events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit()
                    sys.exit()
                # Restart only works on the game-over screen
                if event.key == pygame.K_r and self.game_over:
                    self.reset()

    # ── Spawn logic ───────────────────────────────────────────────────────────
    def _try_spawn_enemy(self) -> None:
        """
        Spawn a new enemy car after ENEMY_SPAWN_DELAY frames.
        As the score increases, the delay shrinks (harder difficulty).
        """
        self._enemy_timer += 1
        if self._enemy_timer >= self._enemy_delay:
            self._enemy_timer = 0
            enemy = EnemyCar(self._img_enemy, self.scroll_speed)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)
            # Gradually reduce spawn delay (min 30 frames ≈ 0.5 s)
            self._enemy_delay = max(30, S.ENEMY_SPAWN_DELAY - self.score // 200)

    def _try_spawn_coin(self) -> None:
        """
        Each frame, roll a random chance to spawn a coin.
        Caps at COIN_MAX_ON_ROAD coins visible at once.
        """
        if len(self.coins) < S.COIN_MAX_ON_ROAD:
            if random.random() < S.COIN_SPAWN_CHANCE:
                coin = Coin(self._img_coin, self.scroll_speed)
                self.coins.add(coin)
                self.all_sprites.add(coin)

    # ── Collision detection ────────────────────────────────────────────────────
    def _check_collisions(self) -> None:
        """
        1. Player ↔ Enemy  → trigger explosion, set game_over flag.
        2. Player ↔ Coin   → collect coin, increment counter.
        """
        # Player hit an enemy?
        hit_enemies = pygame.sprite.spritecollide(
            self.player, self.enemies, dokill=True,
            collided=pygame.sprite.collide_mask   # pixel-perfect
        )
        if hit_enemies:
            # Spawn explosion at player's centre
            explosion = Explosion(self._explosion_frames,
                                  self.player.rect.center)
            self.explosions.add(explosion)
            self.all_sprites.add(explosion)
            # Remove the player sprite from view immediately
            self.player.kill()
            self.game_over = True

        # Player collected a coin?
        collected = pygame.sprite.spritecollide(
            self.player, self.coins, dokill=True   # remove coin on touch
        )
        self.coins_collected += len(collected)
        # Bonus score for each coin
        self.score += len(collected) * 50

    # ── Road scrolling ─────────────────────────────────────────────────────────
    def _scroll_road(self) -> None:
        """
        Advance the road tile downward.
        When the top tile scrolls fully off-screen, wrap it back to the top
        so the road appears infinite.
        """
        self._road_y += int(self.scroll_speed)
        if self._road_y >= self._road_h:
            self._road_y -= self._road_h   # seamless wrap

    def _draw_road(self) -> None:
        """Blit two copies of the road tile for seamless vertical scrolling."""
        # Tile 1 (current)
        self.screen.blit(self._img_road, (0, self._road_y))
        # Tile 2 (one tile above, fills the gap when tile 1 scrolls down)
        self.screen.blit(self._img_road, (0, self._road_y - self._road_h))

    # ── Update / tick ──────────────────────────────────────────────────────────
    def _update(self) -> None:
        """Update all game state for one frame."""
        keys = pygame.key.get_pressed()

        # Ramp up scroll speed over time
        self.scroll_speed = min(
            self.scroll_speed + S.SPEED_INCREMENT,
            S.SCROLL_SPEED_MAX
        )

        # Scroll road
        self._scroll_road()

        # Spawn objects
        self._try_spawn_enemy()
        self._try_spawn_coin()

        # Update all sprites
        self.player.update(keys)
        self.enemies.update(self.scroll_speed)
        self.coins.update(self.scroll_speed)
        self.explosions.update()

        # Collisions
        self._check_collisions()

        # Score: 1 point per frame survived
        self.score += 1

    # ── Draw ───────────────────────────────────────────────────────────────────
    def _draw(self) -> None:
        """Render everything to the screen."""
        # Road
        self._draw_road()

        # All game sprites
        self.all_sprites.draw(self.screen)

        # HUD (always on top of sprites)
        self.hud.draw(self.screen, self.score, self.scroll_speed,
                      self.coins_collected)

        # Game-over overlay
        if self.game_over:
            self.hud.draw_game_over(self.screen, self.score,
                                    self.coins_collected)

        pygame.display.flip()

    # ── Main loop ──────────────────────────────────────────────────────────────
    def run(self) -> None:
        """Start and run the game loop until the window is closed."""
        while True:
            self.clock.tick(S.FPS)
            self._handle_events()

            if not self.game_over:
                self._update()
            else:
                # On game-over: explosions still animate, enemies still move
                self.explosions.update()

            self._draw()


# ════════════════════════════════════════════════════════════════════════════
#  Entry point
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Ensure assets exist before starting
    import os
    if not os.path.exists(S.asset("player_car.png")):
        print("[INFO] Generating assets …")
        import generate_assets   # noqa: F401
        print("[INFO] Assets ready. Starting game …")

    game = Game()
    game.run()
