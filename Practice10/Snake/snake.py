"""
snake.py
========
Core game-logic classes for the Snake game.
No Pygame rendering here — only pure data and rules.

Classes:
  Direction  — named direction constants + opposite-check helper
  Snake      — the snake's body, movement, growth, and self-collision
  Food       — random food placement that avoids walls and the snake body
  LevelSystem — tracks score, level, and speed progression
"""

import random
import settings as S


# ════════════════════════════════════════════════════════════════════════════
#  Direction constants
# ════════════════════════════════════════════════════════════════════════════
class Direction:
    """
    Simple namespace for the four movement directions.
    Each value is a (dx, dy) tuple in grid-cell units.
    """
    UP    = ( 0, -1)
    DOWN  = ( 0,  1)
    LEFT  = (-1,  0)
    RIGHT = ( 1,  0)

    @staticmethod
    def opposite(a: tuple, b: tuple) -> bool:
        """Return True if direction 'b' is the exact reverse of 'a'."""
        return a[0] + b[0] == 0 and a[1] + b[1] == 0


# ════════════════════════════════════════════════════════════════════════════
#  Snake
# ════════════════════════════════════════════════════════════════════════════
class Snake:
    """
    Represents the snake as a deque-like list of (col, row) cells.

    Index 0 is always the HEAD.
    The snake grows by NOT removing the tail on the frame it eats food.

    Attributes:
        body    – list of (col, row) tuples, head first
        dir     – current (dx, dy) movement direction
        alive   – False once a lethal collision is detected
        grew    – True for the frame after food is eaten (tail not removed)
    """

    def __init__(self):
        # Build initial body: head at start pos, tail extends LEFT
        cx, cy = S.SNAKE_START_X, S.SNAKE_START_Y
        self.body = [(cx - i, cy) for i in range(S.SNAKE_START_LEN)]
        self.dir   = S.SNAKE_START_DIR   # moving right by default
        self.alive = True
        self.grew  = False               # flag: did we just eat?

    def change_direction(self, new_dir: tuple) -> None:
        """
        Queue a direction change.
        Ignores 180° reversals (snake can't turn into itself).
        """
        if not Direction.opposite(self.dir, new_dir):
            self.dir = new_dir

    def move(self) -> None:
        """
        Advance the snake one cell in self.dir.
        - Prepend the new head position.
        - Remove the tail UNLESS the snake just ate (grew flag).
        - Detect wall collision and self-collision; sets self.alive = False.
        """
        head_col, head_row = self.body[0]
        dx, dy = self.dir

        # New head position
        new_head = (head_col + dx, head_row + dy)

        # ── Wall / border collision ──────────────────────────────────────────
        # The playfield is surrounded by a wall of WALL_THICKNESS cells.
        # If the new head exits the inner play area → game over.
        nc, nr = new_head
        if (nc < S.PLAY_LEFT or nc > S.PLAY_RIGHT or
                nr < S.PLAY_TOP  or nr > S.PLAY_BOTTOM):
            self.alive = False
            return                # stop here; don't update body

        # ── Self collision ───────────────────────────────────────────────────
        # Check against the body EXCLUDING the very last tail cell,
        # because that cell will be removed before the new head occupies space.
        # (If the snake grew, the tail stays — include the full body.)
        check_body = self.body if self.grew else self.body[:-1]
        if new_head in check_body:
            self.alive = False
            return

        # ── Apply movement ───────────────────────────────────────────────────
        self.body.insert(0, new_head)   # add new head

        if self.grew:
            self.grew = False           # consumed the grow flag; keep tail
        else:
            self.body.pop()             # remove tail to keep length constant

    def grow(self) -> None:
        """Signal that the snake should grow on its next move."""
        self.grew = True

    @property
    def head(self) -> tuple:
        """Convenience: the current head (col, row)."""
        return self.body[0]

    def occupies(self, cell: tuple) -> bool:
        """Return True if the given cell is any part of the snake body."""
        return cell in self.body


# ════════════════════════════════════════════════════════════════════════════
#  Food
# ════════════════════════════════════════════════════════════════════════════
class Food:
    """
    A single food pellet placed at a random grid cell.

    Placement rules:
      • Must be inside the inner play area (not on the wall border)
      • Must not overlap any part of the snake body
    If the grid is completely full (no free cells), pos is set to None.
    """

    def __init__(self, snake: Snake):
        self.pos = self._random_pos(snake)

    def _random_pos(self, snake: Snake) -> tuple | None:
        """
        Choose a random free cell within the play area.
        Returns None if no free cell exists (very unlikely in normal play).
        """
        # Build the set of all inner cells
        all_cells = {
            (c, r)
            for c in range(S.PLAY_LEFT,  S.PLAY_RIGHT  + 1)
            for r in range(S.PLAY_TOP,   S.PLAY_BOTTOM + 1)
        }
        # Remove cells occupied by the snake
        free = all_cells - set(snake.body)

        if not free:
            return None   # edge case: grid is completely full

        return random.choice(list(free))

    def respawn(self, snake: Snake) -> None:
        """Place food at a new random free position."""
        self.pos = self._random_pos(snake)


# ════════════════════════════════════════════════════════════════════════════
#  LevelSystem
# ════════════════════════════════════════════════════════════════════════════
class LevelSystem:
    """
    Manages score, level, and movement speed.

    Speed is expressed in *moves per second*.
    The game loop uses a fixed-step timer based on this value.

    Levels advance every FOOD_PER_LEVEL foods eaten.
    """

    def __init__(self):
        self.score        = 0
        self.level        = 1
        self.foods_eaten  = 0     # total foods consumed (across all levels)
        self._foods_this_level = 0   # count within the current level
        self.speed        = S.SPEED_INIT    # moves per second
        self.level_up_flash = 0   # countdown timer for level-up visual flash

    def eat(self) -> bool:
        """
        Call when the snake eats a food pellet.
        Awards score and checks for level advancement.
        Returns True if this food triggered a level-up.
        """
        # Score = base points × current level (higher levels = more points)
        self.score += S.POINTS_PER_FOOD * (S.POINTS_LEVEL_MULT * self.level)
        self.foods_eaten += 1
        self._foods_this_level += 1

        # Level-up check
        if self._foods_this_level >= S.FOOD_PER_LEVEL:
            self._foods_this_level = 0
            self.level += 1
            # Raise speed, respecting the hard cap
            self.speed = min(self.speed + S.SPEED_INCREMENT, S.SPEED_MAX)
            self.level_up_flash = 45   # ~0.75 s at 60 fps
            return True               # level-up occurred

        return False

    def tick_flash(self) -> None:
        """Decrement the level-up flash timer each display frame."""
        if self.level_up_flash > 0:
            self.level_up_flash -= 1

    @property
    def move_interval_ms(self) -> float:
        """
        Milliseconds between snake moves.
        Used by the game loop's fixed-step timer.
        """
        return 1000.0 / self.speed
