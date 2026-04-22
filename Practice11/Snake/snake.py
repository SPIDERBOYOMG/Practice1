"""
snake.py
========
Core game-logic classes for the Snake game.
No Pygame rendering here — only pure data and rules.

Classes
-------
  Direction    — named direction constants + opposite-check helper
  Snake        — the snake's body, movement, growth, and collision detection
  FoodItem     — a single food pellet with a type, position, and countdown timer
  FoodManager  — manages spawning, ticking, and expiry of multiple food items
  LevelSystem  — tracks score, level, and speed progression

New in Practice 8 extension
----------------------------
  • FoodItem   : each piece of food now has a *type* (FoodConfig) that defines
                 its point weight, colour, and how long it lives before expiring.
  • FoodManager: replaces the old single-Food class.
                 Spawns up to MAX_FOOD_ON_SCREEN items simultaneously using
                 weighted-random selection from FOOD_TYPES.
                 Ticks each item's countdown timer every game step and removes
                 items whose timer reaches zero.
"""

import random
import settings as S
from settings import FoodConfig


# ════════════════════════════════════════════════════════════════════════════
#  Direction
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
        """Return True if direction b is the exact reverse of direction a."""
        return a[0] + b[0] == 0 and a[1] + b[1] == 0


# ════════════════════════════════════════════════════════════════════════════
#  Snake
# ════════════════════════════════════════════════════════════════════════════

class Snake:
    """
    Represents the snake as a list of (col, row) grid cells.

    Index 0 is always the HEAD.
    The snake grows by NOT removing the tail on the frame it eats food.
    `grow_pending` counts how many extra segments are still to be added;
    this allows multi-segment growth (e.g. golden food grows by 2 cells).

    Attributes
    ----------
    body         : list of (col, row) tuples, head-first
    dir          : current (dx, dy) movement direction
    alive        : False once a lethal collision is detected
    grow_pending : number of extra segments still queued to be added
    """

    def __init__(self):
        # Build the initial body: head at start position, tail extends left
        cx, cy = S.SNAKE_START_X, S.SNAKE_START_Y
        self.body        = [(cx - i, cy) for i in range(S.SNAKE_START_LEN)]
        self.dir         = S.SNAKE_START_DIR   # moving right by default
        self.alive       = True
        self.grow_pending = 0   # segments still queued to grow

    def change_direction(self, new_dir: tuple) -> None:
        """
        Apply a direction change request.
        Ignores 180° reversals — the snake cannot turn directly into itself.
        """
        if not Direction.opposite(self.dir, new_dir):
            self.dir = new_dir

    def move(self) -> None:
        """
        Advance the snake one cell in self.dir.

        Steps:
          1. Compute the new head position.
          2. Check wall collision (outside play area → die).
          3. Check self collision (head overlaps body → die).
          4. Prepend new head, remove tail (unless growing).
        """
        head_col, head_row = self.body[0]
        dx, dy = self.dir
        new_head = (head_col + dx, head_row + dy)

        # ── Wall / border collision ──────────────────────────────────────────
        # The play area is bounded by wall cells; new_head must stay inside.
        nc, nr = new_head
        if (nc < S.PLAY_LEFT  or nc > S.PLAY_RIGHT or
                nr < S.PLAY_TOP   or nr > S.PLAY_BOTTOM):
            self.alive = False
            return   # halt immediately; do not update body

        # ── Self collision ───────────────────────────────────────────────────
        # Exclude the last tail cell from the check when NOT growing, because
        # that cell will be vacated before the head arrives there.
        check_body = self.body if self.grow_pending > 0 else self.body[:-1]
        if new_head in check_body:
            self.alive = False
            return

        # ── Apply movement ───────────────────────────────────────────────────
        self.body.insert(0, new_head)   # prepend new head

        if self.grow_pending > 0:
            # One queued growth segment consumed — keep the tail this frame
            self.grow_pending -= 1
        else:
            self.body.pop()   # remove tail to keep length constant

    def grow(self, segments: int = 1) -> None:
        """
        Queue *segments* extra cells to be added on upcoming moves.
        Calling grow(2) makes the snake grow by 2 cells over 2 move steps.
        """
        self.grow_pending += max(1, segments)

    @property
    def head(self) -> tuple:
        """Convenience property: the current head cell as (col, row)."""
        return self.body[0]

    def occupies(self, cell: tuple) -> bool:
        """Return True if *cell* is any part of the snake's body."""
        return cell in self.body


# ════════════════════════════════════════════════════════════════════════════
#  FoodItem  (NEW — replaces old Food class)
# ════════════════════════════════════════════════════════════════════════════

class FoodItem:
    """
    One piece of food on the grid.

    Each item has:
      • a grid position (col, row)
      • a FoodConfig that defines its weight, colours, and starting lifetime
      • a countdown timer (time_left_ms) that ticks down each game step

    When time_left_ms reaches 0 the item is considered expired and should be
    removed from the grid by FoodManager.

    Attributes
    ----------
    pos          : (col, row) grid cell
    config       : FoodConfig describing this food's properties
    max_time_ms  : total lifetime in milliseconds (cached from config)
    time_left_ms : remaining milliseconds before this item expires
    """

    def __init__(self, pos: tuple, config: FoodConfig):
        self.pos          = pos
        self.config       = config
        # Convert seconds → milliseconds for consistency with pygame's dt
        self.max_time_ms  = config.lifetime_s * 1_000.0
        self.time_left_ms = self.max_time_ms

    def tick(self, dt_ms: float) -> None:
        """
        Subtract *dt_ms* elapsed milliseconds from the remaining lifetime.
        The timer is clamped at 0 so it never goes negative.
        """
        self.time_left_ms = max(0.0, self.time_left_ms - dt_ms)

    @property
    def expired(self) -> bool:
        """True once the countdown has reached zero."""
        return self.time_left_ms <= 0.0

    @property
    def lifetime_fraction(self) -> float:
        """
        Remaining lifetime expressed as a 0.0–1.0 fraction.
        1.0 = just spawned (full time left).
        0.0 = expired (no time left).
        """
        if self.max_time_ms <= 0:
            return 1.0
        return self.time_left_ms / self.max_time_ms

    @property
    def is_blinking(self) -> bool:
        """
        True when the item is close to expiry (below FOOD_BLINK_THRESHOLD).
        The renderer uses this flag to blink the sprite as a warning.
        """
        return self.lifetime_fraction <= S.FOOD_BLINK_THRESHOLD


# ════════════════════════════════════════════════════════════════════════════
#  FoodManager  (NEW — replaces old Food class)
# ════════════════════════════════════════════════════════════════════════════

class FoodManager:
    """
    Manages the collection of food items currently on the grid.

    Responsibilities
    ----------------
    1. Spawn new food items using weighted-random type selection, up to
       S.MAX_FOOD_ON_SCREEN items at a time.
    2. Tick every item's countdown timer each game step.
    3. Remove items whose timer has expired.
    4. Guarantee food never overlaps the snake body or other food items.

    Attributes
    ----------
    items         : list of active FoodItem objects
    _spawn_accum  : accumulated ms since the last spawn attempt
    """

    def __init__(self, snake: Snake):
        # Start with one food item already on the grid
        self.items: list[FoodItem] = []
        self._spawn_accum: float   = 0.0

        # Spawn the initial item immediately
        self._try_spawn(snake)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _free_cells(self, snake: Snake) -> list[tuple]:
        """
        Return a list of all grid cells that are neither occupied by the snake
        nor already holding a food item.  Used by the spawner to find safe
        positions for new food.
        """
        # All cells inside the play area
        all_cells = {
            (c, r)
            for c in range(S.PLAY_LEFT,  S.PLAY_RIGHT  + 1)
            for r in range(S.PLAY_TOP,   S.PLAY_BOTTOM + 1)
        }
        # Remove snake body cells
        occupied = set(snake.body)
        # Remove cells already holding food
        for item in self.items:
            occupied.add(item.pos)

        return list(all_cells - occupied)

    def _pick_food_type(self) -> FoodConfig:
        """
        Choose a food type using weighted-random selection based on each
        FoodConfig's spawn_weight.

        Example: weights [50, 30, 10] → apple chosen ~56 % of the time.
        This uses the same algorithm as random.choices() but is explicit
        so it's easy to follow and debug.
        """
        types   = S.FOOD_TYPES
        weights = [ft.spawn_weight for ft in types]
        total   = sum(weights)

        # Draw a random number in [0, total) and walk the cumulative sum
        roll = random.random() * total
        cumulative = 0
        for ft, w in zip(types, weights):
            cumulative += w
            if roll < cumulative:
                return ft

        # Fallback — should never reach here, but return the first type safely
        return types[0]

    def _try_spawn(self, snake: Snake) -> bool:
        """
        Attempt to place a new food item on a random free cell.
        Does nothing and returns False if:
          • the grid is full (no free cells), or
          • MAX_FOOD_ON_SCREEN items are already present.
        Returns True if a new item was successfully placed.
        """
        # Check the item count cap
        if len(self.items) >= S.MAX_FOOD_ON_SCREEN:
            return False

        free = self._free_cells(snake)
        if not free:
            return False   # every cell is occupied — extremely rare

        # Pick a random position and a weighted-random food type
        pos    = random.choice(free)
        config = self._pick_food_type()
        self.items.append(FoodItem(pos, config))
        return True

    # ── Public interface ──────────────────────────────────────────────────────

    def tick(self, dt_ms: float, snake: Snake) -> None:
        """
        Advance the food system by *dt_ms* milliseconds (one game step).

        Steps
        -----
        1. Count down every active item's timer.
        2. Purge any expired items.
        3. Accumulate time for the spawn cooldown; try to spawn when ready.
        """
        # 1. Tick each item's timer
        for item in self.items:
            item.tick(dt_ms)

        # 2. Remove expired items (filter keeps only items that are NOT expired)
        self.items = [item for item in self.items if not item.expired]

        # 3. Spawn cooldown — attempt a new spawn every FOOD_SPAWN_INTERVAL_MS
        self._spawn_accum += dt_ms
        if self._spawn_accum >= S.FOOD_SPAWN_INTERVAL_MS:
            self._spawn_accum = 0.0
            self._try_spawn(snake)

    def check_eat(self, snake: Snake) -> FoodItem | None:
        """
        Check whether the snake's head overlaps any food item.
        If so, remove that item from the list and return it.
        Returns None if the head is not on any food.

        The caller (Game._step) uses the returned item to award score and
        trigger snake growth proportional to the food's weight.
        """
        head = snake.head
        for item in self.items:
            if item.pos == head:
                self.items.remove(item)   # consume the item
                # Immediately try to spawn a replacement
                self._try_spawn(snake)
                return item
        return None   # nothing eaten this step

    def ensure_food(self, snake: Snake) -> None:
        """
        Guarantee at least one food item exists on the grid.
        Called after resets to avoid an empty board.
        """
        if not self.items:
            self._try_spawn(snake)


# ════════════════════════════════════════════════════════════════════════════
#  LevelSystem
# ════════════════════════════════════════════════════════════════════════════

class LevelSystem:
    """
    Manages score, level, and movement speed.

    Levels advance every FOOD_PER_LEVEL apples eaten.
    Speed (moves per second) increases with each level up to SPEED_MAX.

    The score awarded per food is:
        POINTS_PER_FOOD × food.config.weight × (POINTS_LEVEL_MULT × level)
    so heavier food types and higher levels both multiply the score.
    """

    def __init__(self):
        self.score             = 0
        self.level             = 1
        self.foods_eaten       = 0    # total across all levels
        self._foods_this_level = 0    # counter within the current level
        self.speed             = S.SPEED_INIT
        self.level_up_flash    = 0    # countdown frames for the level-up banner

    def eat(self, food_item: FoodItem) -> bool:
        """
        Award score for eating *food_item* and check for a level-up.

        Score formula:
            base_pts × food_weight × (level_mult × level)

        Parameters
        ----------
        food_item : the FoodItem that was just consumed

        Returns
        -------
        True if this food triggered a level-up, False otherwise.
        """
        # Award points: base × food weight × current level
        pts = (S.POINTS_PER_FOOD
               * food_item.config.weight
               * (S.POINTS_LEVEL_MULT * self.level))
        self.score += pts

        self.foods_eaten       += 1
        self._foods_this_level += 1

        # Level-up check: every FOOD_PER_LEVEL items eaten
        if self._foods_this_level >= S.FOOD_PER_LEVEL:
            self._foods_this_level = 0
            self.level += 1
            self.speed  = min(self.speed + S.SPEED_INCREMENT, S.SPEED_MAX)
            self.level_up_flash = 45   # ~0.75 s at 60 fps
            return True   # level-up occurred

        return False

    def tick_flash(self) -> None:
        """Decrement the level-up banner flash timer once per display frame."""
        if self.level_up_flash > 0:
            self.level_up_flash -= 1

    @property
    def move_interval_ms(self) -> float:
        """
        Milliseconds between snake moves, derived from moves-per-second speed.
        The game loop uses this as the fixed-step interval.
        """
        return 1000.0 / self.speed
