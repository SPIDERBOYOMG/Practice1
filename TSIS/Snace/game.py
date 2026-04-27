"""
game.py
=======
Game coordinator for TSIS 4 Snake.

Owns the active game session: snake, food, power-ups, obstacles, level system.
Called by main.py's screen-manager when the STATE_PLAYING state is active.

Public interface
----------------
  Game.reset(username, personal_best)  — start a fresh session
  Game.handle_event(event)             — feed pygame events; returns action str or None
  Game.update(dt_ms)                   — one frame of game logic
  Game.draw(renderer)                  — render everything
  Game.score / Game.level              — read-only properties for game-over screen
"""

import pygame
import config as C
from snake import (Snake, FoodManager, PowerUpManager, ObstacleManager,
                   LevelSystem, Direction)
import db


class Game:
    """
    Coordinates all sub-systems for one play session.

    Returns
    -------
    handle_event() returns one of:
      None         — nothing special
      "GAME_OVER"  — player died; caller should switch to game-over screen
    """

    def __init__(self):
        self._username     : str  = "PLAYER"
        self._personal_best: int  = 0
        self.reset(self._username, self._personal_best)

    def reset(self, username: str, personal_best: int) -> None:
        self._username      = username
        self._personal_best = personal_best

        self.snake      = Snake()
        self.level_sys  = LevelSystem()
        self.food_mgr   = FoodManager(self.snake)
        self.powerup_mgr = PowerUpManager()
        self.obstacle_mgr = ObstacleManager()

        self.move_accumulator = 0.0
        self._queued_dir      = self.snake.dir
        self.game_over        = False
        self._result_saved    = False

    # ── Read-only properties ──────────────────────────────────────────────────

    @property
    def score(self) -> int:
        return self.level_sys.score

    @property
    def level(self) -> int:
        return self.level_sys.level

    @property
    def personal_best(self) -> int:
        return self._personal_best

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """
        Process a single pygame event.
        Returns "GAME_OVER" when the snake dies (already saved to DB).
        Returns "MENU" if the player presses M on the game-over screen.
        """
        if event.type != pygame.KEYDOWN:
            return None

        if self.game_over:
            if event.key == pygame.K_r:
                return "RETRY"
            if event.key in (pygame.K_m,):
                return "MENU"
            return None

        # Direction buffering
        key_to_dir = {
            pygame.K_UP: Direction.UP,    pygame.K_w: Direction.UP,
            pygame.K_DOWN: Direction.DOWN, pygame.K_s: Direction.DOWN,
            pygame.K_LEFT: Direction.LEFT, pygame.K_a: Direction.LEFT,
            pygame.K_RIGHT: Direction.RIGHT, pygame.K_d: Direction.RIGHT,
        }
        if event.key in key_to_dir:
            nd = key_to_dir[event.key]
            if not Direction.opposite(self.snake.dir, nd):
                self._queued_dir = nd

        return None

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt_ms: float) -> str | None:
        """
        Advance game logic by *dt_ms* real milliseconds.
        Returns "GAME_OVER" once when the snake dies (only on the first call).
        """
        if self.game_over:
            return None

        # Apply speed from power-up
        self.level_sys.apply_speed_modifier(self.powerup_mgr)

        self.move_accumulator += dt_ms
        interval = self.level_sys.move_interval_ms

        if self.move_accumulator >= interval:
            self.move_accumulator -= interval
            result = self._step(interval)
            if result == "GAME_OVER":
                return "GAME_OVER"

        self.level_sys.tick_flash()
        return None

    def _step(self, dt_ms: float) -> str | None:
        """One logical snake-move step."""
        self.snake.change_direction(self._queued_dir)

        # Move snake (passes obstacle blocks for collision checking)
        self.snake.move(obstacles=self.obstacle_mgr.blocks)

        if not self.snake.alive:
            self._trigger_game_over()
            return "GAME_OVER"

        # Tick food
        food_pos = {i.pos for i in self.food_mgr.items}
        self.food_mgr.tick(dt_ms, self.snake, self.obstacle_mgr.blocks)

        # Update power-up system
        self.powerup_mgr.update(self.snake, self.obstacle_mgr.blocks, food_pos)

        # Check power-up collection
        self.powerup_mgr.check_collect(self.snake)

        # Check food eaten
        eaten = self.food_mgr.check_eat(self.snake, self.obstacle_mgr.blocks)
        if eaten is not None:
            if eaten.config.is_poison:
                # Poison: shorten snake
                self.snake.shorten(C.POISON_SHORTEN)
                if not self.snake.alive:
                    self._trigger_game_over()
                    return "GAME_OVER"
            else:
                # Normal food: award points and maybe level up
                leveled_up = self.level_sys.eat(eaten)
                grow_segs  = 1 + (eaten.config.weight - 1) // 3
                self.snake.grow(grow_segs)

                if leveled_up:
                    # Place new obstacles for the new level
                    self.obstacle_mgr.update_for_level(
                        self.level_sys.level, self.snake,
                        {i.pos for i in self.food_mgr.items},
                    )

        self.food_mgr.ensure_food(self.snake, self.obstacle_mgr.blocks)
        return None

    def _trigger_game_over(self) -> None:
        self.game_over = True
        # Update personal best
        if self.level_sys.score > self._personal_best:
            self._personal_best = self.level_sys.score
        # Save to DB (non-fatal if DB is down)
        if not self._result_saved:
            self._result_saved = True
            db.save_session(self._username, self.level_sys.score, self.level_sys.level)

    # ── Render ────────────────────────────────────────────────────────────────

    def draw(self, renderer) -> None:
        renderer.draw_frame(
            snake       = self.snake,
            food_mgr    = self.food_mgr,
            level_sys   = self.level_sys,
            powerup_mgr = self.powerup_mgr,
            obstacle_mgr= self.obstacle_mgr,
            personal_best = self._personal_best,
        )
        if self.game_over:
            renderer.draw_game_over(self.level_sys, self._personal_best)
