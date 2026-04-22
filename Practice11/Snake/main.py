"""
main.py  —  PIXEL SNAKE  (Practice 8 Extended)
===============================================
Classic Snake game built with Pygame.

Features from original Practice 8
------------------------------------
  ✓ Wall / border collision    — snake dies if it leaves the play area
  ✓ Self collision             — snake dies if it runs into its own body
  ✓ Smart food placement       — food never spawns on walls or the snake body
  ✓ Level system               — advance every FOOD_PER_LEVEL apples eaten
  ✓ Speed increase             — each level raises moves-per-second
  ✓ Score counter              — points = base × food_weight × level
  ✓ Level counter              — shown in HUD + "LEVEL UP!" banner
  ✓ Pixel / retro art style    — monospace font, bevelled walls, gradient body

New features added in extension
---------------------------------
  ✓ Multiple food types        — APPLE (×1), CHERRY (×3), GOLDEN (×8)
  ✓ Weighted random food spawn — rarer types give more points but appear less often
  ✓ Up to 3 food items         — several items can be on the grid simultaneously
  ✓ Disappearing food (timers) — each item has a countdown; it vanishes when it expires
  ✓ Timer arc ring             — shrinking arc drawn around each food item
  ✓ Blink warning              — items blink during the final 25 % of their lifetime
  ✓ HUD food indicators        — coloured dots show active items and their weights
  ✓ Multi-segment growth       — heavier foods grow the snake by more segments

Controls
--------
  Arrow keys / WASD   move the snake
  R                   restart after Game Over
  Q / ESC             quit
"""

import sys
import pygame

import settings as S
from snake    import Snake, FoodManager, LevelSystem, Direction
from renderer import Renderer


# ════════════════════════════════════════════════════════════════════════════
#  Game  — owns the main loop and coordinates all sub-systems
# ════════════════════════════════════════════════════════════════════════════

class Game:
    """
    Top-level game coordinator.

    Owns references to Snake, FoodManager, LevelSystem, and Renderer.
    Runs the classic pygame loop: handle events → update → render.

    Movement uses a fixed-step timer (move_accumulator) so the snake steps
    at exactly `level_sys.speed` moves per second regardless of display FPS.
    """

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(S.TITLE)

        # Window height = game grid + HUD bar underneath
        total_h = S.WIN_H + S.HUD_H
        self.screen = pygame.display.set_mode((S.WIN_W, total_h),
                                              pygame.SCALED)
        self.clock  = pygame.time.Clock()

        # Renderer is created once; it pre-bakes static wall/grid surfaces
        self.renderer = Renderer(self.screen)

        self._reset()

    # ── Reset / initialise game state ─────────────────────────────────────────

    def _reset(self) -> None:
        """
        Create fresh Snake, FoodManager, and LevelSystem objects.
        Called both at startup and when the player presses R after game-over.
        """
        self.snake     = Snake()
        self.level_sys = LevelSystem()

        # FoodManager replaces the old single Food object.
        # It starts by spawning one item and will add more over time.
        self.food_mgr  = FoodManager(self.snake)

        # move_accumulator: elapsed ms since the last snake step.
        # When it exceeds move_interval_ms the snake takes one step.
        self.move_accumulator = 0.0

        # Buffer the latest direction key press between move steps so rapid
        # key presses are never lost between frames.
        self._queued_dir = self.snake.dir

        self.game_over = False

    # ── Input handling ────────────────────────────────────────────────────────

    def _handle_events(self) -> None:
        """
        Process all OS events (quit, keyboard) for the current frame.
        Direction changes are buffered in _queued_dir and applied just
        before the next snake move to prevent missed inputs.
        """
        for event in pygame.event.get():

            # Window close button
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                # Quit at any time
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit()
                    sys.exit()

                # Restart only works after game-over
                if event.key == pygame.K_r and self.game_over:
                    self._reset()
                    return

                # Direction keys — buffer the most recently pressed key.
                # The direction is validated against the current one to
                # prevent illegal 180° reversals.
                key_to_dir = {
                    pygame.K_UP    : Direction.UP,
                    pygame.K_w     : Direction.UP,
                    pygame.K_DOWN  : Direction.DOWN,
                    pygame.K_s     : Direction.DOWN,
                    pygame.K_LEFT  : Direction.LEFT,
                    pygame.K_a     : Direction.LEFT,
                    pygame.K_RIGHT : Direction.RIGHT,
                    pygame.K_d     : Direction.RIGHT,
                }
                if event.key in key_to_dir:
                    new_dir = key_to_dir[event.key]
                    # Only apply if the new direction is not a 180° reversal
                    if not Direction.opposite(self.snake.dir, new_dir):
                        self._queued_dir = new_dir

    # ── Update (one logical game step) ────────────────────────────────────────

    def _step(self, dt_ms: float) -> None:
        """
        Advance the game by one snake-move step.

        Called only when move_accumulator >= move_interval_ms.

        Steps
        -----
        1. Apply the buffered direction change.
        2. Move the snake (wall + self-collision checked internally).
        3. If the snake died, set game_over.
        4. Tick all food timers and remove expired items.
        5. Check if the snake's new head position is on any food item.
           If so: award score proportional to food weight × level,
                  grow the snake (more segments for heavier food),
                  and trigger a level-up check.
        6. Ensure at least one food item remains on the grid.
        """
        # 1. Apply the buffered direction
        self.snake.change_direction(self._queued_dir)

        # 2. Move the snake one cell
        self.snake.move()

        # 3. Check for death
        if not self.snake.alive:
            self.game_over = True
            return   # no further processing needed this step

        # 4. Tick food timers and remove expired items, and possibly spawn new ones.
        #    Pass dt_ms so the manager can run on real elapsed time.
        self.food_mgr.tick(dt_ms, self.snake)

        # 5. Check whether the snake's head landed on any food item
        eaten = self.food_mgr.check_eat(self.snake)
        if eaten is not None:
            # Award score using the food's weight and the current level
            self.level_sys.eat(eaten)

            # Grow the snake by a number of segments proportional to weight.
            # APPLE(×1)→1 seg, CHERRY(×3)→2 segs, GOLDEN(×8)→3 segs.
            # Formula: 1 + (weight - 1) // 3 gives a gentle scaling curve.
            grow_segs = 1 + (eaten.config.weight - 1) // 3
            self.snake.grow(grow_segs)

        # 6. Ensure there is always at least one food on the board.
        #    FoodManager handles this internally, but this is a safety net
        #    in case all items expired simultaneously.
        self.food_mgr.ensure_food(self.snake)

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        """
        Start and run the game loop until the player quits.

        Loop structure
        --------------
        1. Measure elapsed time (dt).
        2. Process input events.
        3. If not game-over: run the fixed-step movement timer and step the game.
        4. Tick the level-up flash timer (every display frame, not every move step).
        5. Render the frame.
        6. Flip the display buffer.
        """
        while True:
            # dt: milliseconds elapsed since the last frame.
            # Capped at 100 ms to prevent the "spiral of death" if the window
            # is moved or the game pauses briefly.
            dt = self.clock.tick(S.FPS_DISPLAY)
            dt = min(dt, 100)

            # 2. Input
            self._handle_events()

            if not self.game_over:
                # 3. Fixed-step movement ─────────────────────────────────────
                # Accumulate real elapsed time; move the snake once per interval.
                self.move_accumulator += dt
                interval = self.level_sys.move_interval_ms

                # Allow at most one move per display frame to prevent catching
                # up with missed steps all at once (spiral-of-death guard).
                if self.move_accumulator >= interval:
                    self.move_accumulator -= interval
                    # Pass the actual elapsed step size to food timers so they
                    # count down in real time (not in frame counts).
                    self._step(interval)

                # 4. Flash timer counts display frames, not move steps
                self.level_sys.tick_flash()

            # 5. Render
            self.renderer.draw_frame(self.snake, self.food_mgr, self.level_sys)

            # 6. Game-over overlay (drawn on top of the normal frame)
            if self.game_over:
                self.renderer.draw_game_over(self.level_sys)

            # 7. Flip double buffer to display
            pygame.display.flip()


# ════════════════════════════════════════════════════════════════════════════
#  Entry point
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    game = Game()
    game.run()
