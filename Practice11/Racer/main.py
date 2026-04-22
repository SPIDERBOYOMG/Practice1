"""
main.py  —  PIXEL RACER  (extended)
=====================================
Top-down pixel-art lane racer.

New features in this version
-----------------------------
1. Weighted coin types
   Four rarity tiers (Bronze / Silver / Gold / Gem) each with a different
   spawn probability (weight), point value, and visual appearance.
   Spawn uses weighted random selection defined in settings.COIN_TYPES.

2. Enemy speed boost on coin milestones
   Every time the player collects ENEMY_BOOST_EVERY_N coins the enemy cars
   gain ENEMY_BOOST_AMOUNT extra px/frame of speed.
   A "DANGER!" banner flashes on-screen to warn the player.
   The boost is capped at ENEMY_SPEED_EXTRA_MAX.

3. Full comments throughout

Controls
--------
  ← / A   move left
  → / D   move right
  R        restart after Game Over
  Q / ESC  quit
"""

import sys
import random
import pygame

import settings as S
from sprites import PlayerCar, EnemyCar, Coin, Explosion, pick_coin_type
from hud     import HUD


# ════════════════════════════════════════════════════════════════════════════
#  Asset helpers
# ════════════════════════════════════════════════════════════════════════════

def load_image(name: str) -> pygame.Surface:
    """
    Load a PNG from the assets folder.
    Runs generate_assets.py automatically if the file is missing.
    """
    path = S.asset(name)
    try:
        return pygame.image.load(path).convert_alpha()
    except FileNotFoundError:
        import os, runpy
        # Run generate_assets.py by absolute path so it works regardless
        # of the working directory Python was launched from.
        _gen = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "generate_assets.py")
        print(f"[INFO] '{name}' not found – running generate_assets.py …")
        runpy.run_path(_gen)
        return pygame.image.load(path).convert_alpha()


def load_explosion_frames() -> list[pygame.Surface]:
    """Return a list of the 4 explosion frame surfaces."""
    return [load_image(f"explosion_{i}.png") for i in range(4)]


# ════════════════════════════════════════════════════════════════════════════
#  Game
# ════════════════════════════════════════════════════════════════════════════

class Game:
    """
    Owns the entire game state and drives the main loop.

    State is split into:
      • Sprite groups  (all_sprites, enemies, coins, explosions)
      • Scalars        (scroll_speed, score, coins_count, …)
      • Boost system   (_enemy_extra, _boost_threshold, _danger_timer)
    """

    def __init__(self):
        pygame.init()
        # SCALED flag keeps integer pixel-perfect rendering when the
        # window is resized or run on high-DPI displays
        self.screen = pygame.display.set_mode((S.WIN_W, S.WIN_H), pygame.SCALED)
        pygame.display.set_caption(S.TITLE)
        self.clock  = pygame.time.Clock()

        # ── Load assets once; reused across resets ────────────────────────
        self._img_player       = load_image("player_car.png")
        self._img_enemy        = load_image("enemy_car.png")
        self._img_road         = load_image("road_bg.png")
        self._explosion_frames = load_explosion_frames()

        # HUD no longer needs a coin image (coins are drawn procedurally)
        self.hud = HUD()

        self.reset()

    # ── Reset ─────────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reinitialise all mutable game state for a fresh run."""

        # ── Sprite groups ─────────────────────────────────────────────────
        self.all_sprites = pygame.sprite.Group()
        self.enemies     = pygame.sprite.Group()
        self.coins       = pygame.sprite.Group()
        self.explosions  = pygame.sprite.Group()

        # ── Player ────────────────────────────────────────────────────────
        self.player = PlayerCar(self._img_player)
        self.all_sprites.add(self.player)

        # ── Scrolling road ────────────────────────────────────────────────
        self._road_h = self._img_road.get_height()   # tile height (600 px)
        self._road_y = 0   # Y position of the first tile (second = y - h)

        # ── Passive difficulty ramp ───────────────────────────────────────
        self.scroll_speed = float(S.SCROLL_SPEED_INIT)

        # ── Enemy spawn timer ─────────────────────────────────────────────
        self._enemy_timer = 0
        self._enemy_delay = S.ENEMY_SPAWN_DELAY

        # ── Enemy boost system ────────────────────────────────────────────
        # _enemy_extra: current "extra" speed on top of road scroll.
        # Starts at the value defined in settings; raised by boosts.
        self._enemy_extra      = float(S.ENEMY_SPEED_EXTRA)

        # _boost_threshold: the next coins_count value that will trigger a boost.
        # Advances by ENEMY_BOOST_EVERY_N after each boost.
        self._boost_threshold  = S.ENEMY_BOOST_EVERY_N

        # _danger_timer: countdown (frames) for the DANGER banner visibility.
        # Set to ENEMY_BOOST_FLASH_FRAMES when a boost fires; decremented each frame.
        self._danger_timer     = 0

        # ── Score & coin tracking ─────────────────────────────────────────
        self.score       = 0    # total score (frame survival + coin value)
        self.coins_count = 0    # total coins collected (count, used for boost)
        self.coin_value  = 0    # total weighted value from collected coins

        # Last coin type collected — drives the HUD pickup indicator colour
        self._last_coin_type: dict | None = None

        # ── State flags ───────────────────────────────────────────────────
        self.game_over = False

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_events(self) -> None:
        """Process window and keyboard events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_r and self.game_over:
                    self.reset()

    # ── Spawning ──────────────────────────────────────────────────────────────

    def _try_spawn_enemy(self) -> None:
        """
        Spawn an enemy car after _enemy_delay frames have elapsed.
        The delay shrinks over time (more enemies as score grows).
        Each spawned car receives the current _enemy_extra speed.
        """
        self._enemy_timer += 1
        if self._enemy_timer >= self._enemy_delay:
            self._enemy_timer = 0
            enemy = EnemyCar(self._img_enemy, self.scroll_speed,
                             self._enemy_extra)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)
            # Reduce spawn gap as score grows, capped at 30 frames (~0.5 s)
            self._enemy_delay = max(30, S.ENEMY_SPAWN_DELAY - self.score // 200)

    def _try_spawn_coin(self) -> None:
        """
        Each frame, roll a random chance to spawn a weighted coin.
        Never exceeds COIN_MAX_ON_ROAD coins on the road at once.

        Coin type is chosen by pick_coin_type() which performs a
        weighted random draw from settings.COIN_TYPES.
        """
        if len(self.coins) < S.COIN_MAX_ON_ROAD:
            if random.random() < S.COIN_SPAWN_CHANCE:
                # pick_coin_type() returns one entry from COIN_TYPES,
                # weighted so bronze spawns 60% of the time, gem only 3%
                ctype = pick_coin_type()
                coin  = Coin(ctype, self.scroll_speed)
                self.coins.add(coin)
                self.all_sprites.add(coin)

    # ── Collision detection ───────────────────────────────────────────────────

    def _check_collisions(self) -> None:
        """
        Handle two collision categories:

        1. Player ↔ Enemy  — spawn explosion, set game_over.
        2. Player ↔ Coin   — collect coin(s), add value to score,
                             count toward the next enemy boost.
        """
        # ── Car crash ─────────────────────────────────────────────────────
        hit = pygame.sprite.spritecollide(
            self.player, self.enemies, dokill=True,
            collided=pygame.sprite.collide_mask   # pixel-perfect
        )
        if hit:
            expl = Explosion(self._explosion_frames, self.player.rect.center)
            self.explosions.add(expl)
            self.all_sprites.add(expl)
            self.player.kill()
            self.game_over = True
            return   # no point checking coins if the game just ended

        # ── Coin pickup ────────────────────────────────────────────────────
        collected = pygame.sprite.spritecollide(
            self.player, self.coins, dokill=True   # remove coin on contact
        )
        for coin in collected:
            self.coins_count += 1               # increment total coin count
            self.coin_value  += coin.value      # add weighted point value
            self.score       += coin.value * 10 # bonus score (value × 10)
            self._last_coin_type = coin.coin_type

            # ── Enemy speed boost check ────────────────────────────────────
            # Fire a boost every time coins_count crosses a multiple of N.
            # _boost_threshold tracks the NEXT milestone to cross.
            if self.coins_count >= self._boost_threshold:
                self._fire_enemy_boost()

    def _fire_enemy_boost(self) -> None:
        """
        Increase enemy speed by ENEMY_BOOST_AMOUNT, cap at the maximum,
        activate the danger warning banner, and advance the threshold.
        """
        # Raise the extra speed, but never exceed the hard cap
        self._enemy_extra = min(
            self._enemy_extra + S.ENEMY_BOOST_AMOUNT,
            S.ENEMY_SPEED_EXTRA_MAX
        )

        # Start the on-screen danger flash countdown
        self._danger_timer = S.ENEMY_BOOST_FLASH_FRAMES

        # Advance threshold so the next boost fires after another N coins
        self._boost_threshold += S.ENEMY_BOOST_EVERY_N

        print(f"[BOOST] coins={self.coins_count}  "
              f"enemy_extra={self._enemy_extra:.1f}  "
              f"next at {self._boost_threshold}")

    # ── Road scrolling ────────────────────────────────────────────────────────

    def _scroll_road(self) -> None:
        """
        Advance the road tile Y by scroll_speed each frame.
        When the tile scrolls fully below the window, wrap it back to the top
        so the road looks infinite.
        """
        self._road_y += int(self.scroll_speed)
        if self._road_y >= self._road_h:
            self._road_y -= self._road_h

    def _draw_road(self) -> None:
        """Blit two copies of the road tile for seamless vertical scrolling."""
        self.screen.blit(self._img_road, (0, self._road_y))
        self.screen.blit(self._img_road, (0, self._road_y - self._road_h))

    # ── Update ────────────────────────────────────────────────────────────────

    def _update(self) -> None:
        """Advance one game frame: input → physics → spawning → collisions."""
        keys = pygame.key.get_pressed()

        # ── Passive speed ramp ────────────────────────────────────────────
        self.scroll_speed = min(
            self.scroll_speed + S.SPEED_INCREMENT,
            S.SCROLL_SPEED_MAX
        )

        # ── Road ──────────────────────────────────────────────────────────
        self._scroll_road()

        # ── Spawn ─────────────────────────────────────────────────────────
        self._try_spawn_enemy()
        self._try_spawn_coin()

        # ── Sprites ───────────────────────────────────────────────────────
        self.player.update(keys)

        # Pass enemy_extra to EnemyCar.update() so existing cars on-screen
        # immediately reflect the latest speed after a boost fires.
        self.enemies.update(self.scroll_speed, self._enemy_extra)
        self.coins.update(self.scroll_speed)
        self.explosions.update()

        # ── Collisions ────────────────────────────────────────────────────
        self._check_collisions()

        # ── Passive score (1 point per frame survived) ────────────────────
        self.score += 1

        # ── Danger timer countdown ────────────────────────────────────────
        if self._danger_timer > 0:
            self._danger_timer -= 1

    # ── Draw ──────────────────────────────────────────────────────────────────

    def _draw(self) -> None:
        """Render the complete frame."""
        self._draw_road()
        self.all_sprites.draw(self.screen)

        # HUD receives all stats needed for display
        self.hud.draw(
            self.screen,
            score          = self.score,
            speed          = self.scroll_speed,
            coins_count    = self.coins_count,
            coin_value     = self.coin_value,
            last_coin_type = self._last_coin_type,
            danger_flash   = self._danger_timer,
            enemy_extra    = self._enemy_extra,
        )

        if self.game_over:
            self.hud.draw_game_over(
                self.screen,
                score       = self.score,
                coins_count = self.coins_count,
                coin_value  = self.coin_value,
            )

        pygame.display.flip()

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start and drive the game loop until the window is closed."""
        while True:
            self.clock.tick(S.FPS)
            self._handle_events()

            if not self.game_over:
                self._update()
            else:
                # After game over: let explosions finish their animations
                self.explosions.update()

            self._draw()


# ════════════════════════════════════════════════════════════════════════════
#  Entry point
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import os, runpy
    # Run generate_assets.py by absolute path — no sys.path manipulation needed.
    if not os.path.exists(S.asset("player_car.png")):
        _gen = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "generate_assets.py")
        print("[INFO] Generating assets …")
        runpy.run_path(_gen)

    game = Game()
    game.run()
