"""
main.py  —  PIXEL SNAKE
========================
Classic Snake game built with Pygame.

Features implemented:
  ✓ Wall / border collision — snake dies if it leaves the play area
  ✓ Self collision          — snake dies if it runs into its own body
  ✓ Smart food placement    — food never spawns on walls or the snake body
  ✓ Level system            — advance every FOOD_PER_LEVEL apples eaten
  ✓ Speed increase          — each level raises moves-per-second
  ✓ Score counter           — points = 10 × level per apple
  ✓ Level counter           — shown in HUD + "LEVEL UP!" banner on advance
  ✓ Pixel / retro art style — monospace font, bevelled walls, gradient body

Controls:
  Arrow keys / WASD   move the snake
  R                   restart after Game Over
  Q / ESC             quit
"""

import sys
import pygame

import settings as S
from snake    import Snake, Food, LevelSystem, Direction
from renderer import Renderer


# ════════════════════════════════════════════════════════════════════════════
#  Game class
# ════════════════════════════════════════════════════════════════════════════

class Game:
    """
    Owns the main loop and coordinates Snake, Food, LevelSystem, and Renderer.

    Movement uses a fixed-step timer (move_accumulator) so the snake steps
    at exactly `level_sys.speed` moves per second regardless of FPS.
    """

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(S.TITLE)

        # Window height includes the HUD bar beneath the grid
        total_h = S.WIN_H + S.HUD_H
        self.screen = pygame.display.set_mode((S.WIN_W, total_h),
                                              pygame.SCALED)
        self.clock  = pygame.time.Clock()

        # Renderer is created once; it pre-builds static wall/grid surfaces
        self.renderer = Renderer(self.screen)

        self._reset()

    # ── Reset / initialise game state ────────────────────────────────────────
    def _reset(self) -> None:
        """Create fresh Snake, Food, and LevelSystem objects."""
        self.snake      = Snake()
        self.level_sys  = LevelSystem()
        self.food       = Food(self.snake)

        # move_accumulator: counts elapsed ms since the last snake step.
        # When it exceeds move_interval_ms the snake takes one step.
        self.move_accumulator = 0.0

        # Pending direction change (buffered to avoid missed inputs between moves)
        self._queued_dir = self.snake.dir

        self.game_over  = False

    # ── Input handling ───────────────────────────────────────────────────────
    def _handle_events(self) -> None:
        """Process OS events and keyboard input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                # Quit
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit()
                    sys.exit()

                # Restart
                if event.key == pygame.K_r and self.game_over:
                    self._reset()
                    return

                # Direction keys — buffer the last pressed direction.
                # The change is applied just before the snake moves, so
                # rapid key presses between steps don't get lost.
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
                    # Validate against current direction (no 180° turns)
                    if not Direction.opposite(self.snake.dir, new_dir):
                        self._queued_dir = new_dir

    # ── Update (one logical tick) ────────────────────────────────────────────
    def _step(self) -> None:
        """
        Advance the snake one cell.
        Called only when move_accumulator >= move_interval_ms.
        """
        # Apply the buffered direction change
        self.snake.change_direction(self._queued_dir)

        # Move the snake (also checks wall + self collision internally)
        self.snake.move()

        # Check result of the move
        if not self.snake.alive:
            # Snake hit a wall or its own body → game over
            self.game_over = True
            return

        # Check if the snake's new head position is on the food
        if self.snake.head == self.food.pos:
            # Snake eats: grow and update score/level
            self.snake.grow()
            leveled_up = self.level_sys.eat()
            # Respawn food at a new random free position
            self.food.respawn(self.snake)

    # ── Main loop ────────────────────────────────────────────────────────────
    def run(self) -> None:
        """Start and run the game loop."""
        while True:
            # dt: milliseconds since the last frame (capped to avoid spiral)
            dt = self.clock.tick(S.FPS_DISPLAY)
            dt = min(dt, 100)   # cap delta time to 100 ms

            self._handle_events()

            if not self.game_over:
                # ── Fixed-step movement ─────────────────────────────────────
                # Accumulate elapsed time; step the snake once per interval.
                self.move_accumulator += dt
                interval = self.level_sys.move_interval_ms

                # Allow at most one step per display frame (prevents spiral-
                # of-death if the game freezes for a moment).
                if self.move_accumulator >= interval:
                    self.move_accumulator -= interval
                    self._step()

                # Tick the level-up flash timer every display frame
                self.level_sys.tick_flash()

            # ── Render ─────────────────────────────────────────────────────
            self.renderer.draw_frame(self.snake, self.food, self.level_sys)

            if self.game_over:
                self.renderer.draw_game_over(self.level_sys)

            pygame.display.flip()


# ════════════════════════════════════════════════════════════════════════════
#  Entry point
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    game = Game()
    game.run()
