"""
snake.py
========
Core game-logic classes for the Snake game — TSIS 4 edition.

Classes
-------
  Direction    — named direction constants + opposite-check helper
  Snake        — body, movement, growth, collision detection
  FoodItem     — a single food pellet (now includes poison variant)
  FoodManager  — manages spawning, ticking, and expiry of food items
  PowerUp      — a single power-up item on the field
  PowerUpManager — manages the single active field power-up and active effects
  ObstacleManager — places and tracks static wall-block obstacles
  LevelSystem  — score, level, speed, and flash banner

New in TSIS 4
-------------
  • Poison food (FoodConfig.is_poison) — shortens snake by POISON_SHORTEN
  • PowerUp / PowerUpManager — speed boost, slow-mo, shield
  • ObstacleManager — random wall blocks from level 3
  • Snake.shorten() — remove tail segments without killing the snake
  • Snake.shield — one-hit protection from wall/self/obstacle collision
"""

import random
import pygame
import config as C
from config import FoodConfig, PowerUpConfig


# ════════════════════════════════════════════════════════════════════════════
#  Direction
# ════════════════════════════════════════════════════════════════════════════

class Direction:
    UP    = ( 0, -1)
    DOWN  = ( 0,  1)
    LEFT  = (-1,  0)
    RIGHT = ( 1,  0)

    @staticmethod
    def opposite(a: tuple, b: tuple) -> bool:
        return a[0] + b[0] == 0 and a[1] + b[1] == 0


# ════════════════════════════════════════════════════════════════════════════
#  Snake
# ════════════════════════════════════════════════════════════════════════════

class Snake:
    """
    The snake's body, movement, growth, and collision detection.

    New in TSIS 4
    -------------
    shield       : bool — if True the next lethal collision is absorbed
    shorten()    — remove tail segments (used by poison food)
    """

    def __init__(self):
        cx, cy = C.SNAKE_START_X, C.SNAKE_START_Y
        self.body         = [(cx - i, cy) for i in range(C.SNAKE_START_LEN)]
        self.dir          = C.SNAKE_START_DIR
        self.alive        = True
        self.grow_pending = 0
        self.shield       = False   # NEW: shield power-up flag

    def change_direction(self, new_dir: tuple) -> None:
        if not Direction.opposite(self.dir, new_dir):
            self.dir = new_dir

    def move(self, obstacles: set | None = None) -> None:
        """
        Advance one cell.  Checks wall, self, and obstacle collisions.
        If `self.shield` is True the first lethal collision is absorbed
        (shield consumed, snake survives).
        """
        head_col, head_row = self.body[0]
        dx, dy = self.dir
        new_head = (head_col + dx, head_row + dy)
        nc, nr = new_head

        def _die():
            """Consume shield if available, otherwise kill snake."""
            if self.shield:
                self.shield = False   # shield absorbed the hit
                return False          # survived
            self.alive = False
            return True               # dead

        # ── Wall collision ───────────────────────────────────────────────────
        if (nc < C.PLAY_LEFT or nc > C.PLAY_RIGHT or
                nr < C.PLAY_TOP or nr > C.PLAY_BOTTOM):
            if _die():
                return

        # ── Obstacle collision ───────────────────────────────────────────────
        if obstacles and new_head in obstacles:
            if _die():
                return

        # ── Self collision ───────────────────────────────────────────────────
        check_body = self.body if self.grow_pending > 0 else self.body[:-1]
        if new_head in check_body:
            if _die():
                return

        # ── Apply movement ───────────────────────────────────────────────────
        self.body.insert(0, new_head)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()

    def grow(self, segments: int = 1) -> None:
        self.grow_pending += max(1, segments)

    def shorten(self, segments: int) -> None:
        """
        Remove *segments* tail cells.
        If this would reduce the snake to length ≤ 1, mark it dead
        (the game-over condition for poison).
        """
        for _ in range(segments):
            if len(self.body) <= 1:
                self.alive = False
                return
            self.body.pop()
        if len(self.body) <= 0:
            self.alive = False

    @property
    def head(self) -> tuple:
        return self.body[0]

    def occupies(self, cell: tuple) -> bool:
        return cell in self.body


# ════════════════════════════════════════════════════════════════════════════
#  FoodItem
# ════════════════════════════════════════════════════════════════════════════

class FoodItem:
    def __init__(self, pos: tuple, config: FoodConfig):
        self.pos          = pos
        self.config       = config
        self.max_time_ms  = config.lifetime_s * 1_000.0
        self.time_left_ms = self.max_time_ms

    def tick(self, dt_ms: float) -> None:
        self.time_left_ms = max(0.0, self.time_left_ms - dt_ms)

    @property
    def expired(self) -> bool:
        return self.time_left_ms <= 0.0

    @property
    def lifetime_fraction(self) -> float:
        if self.max_time_ms <= 0:
            return 1.0
        return self.time_left_ms / self.max_time_ms

    @property
    def is_blinking(self) -> bool:
        return self.lifetime_fraction <= C.FOOD_BLINK_THRESHOLD


# ════════════════════════════════════════════════════════════════════════════
#  FoodManager
# ════════════════════════════════════════════════════════════════════════════

class FoodManager:
    def __init__(self, snake: Snake, obstacles: set | None = None):
        self.items: list[FoodItem] = []
        self._spawn_accum: float   = 0.0
        self._try_spawn(snake, obstacles)

    def _free_cells(self, snake: Snake, obstacles: set | None) -> list[tuple]:
        all_cells = {
            (c, r)
            for c in range(C.PLAY_LEFT, C.PLAY_RIGHT + 1)
            for r in range(C.PLAY_TOP,  C.PLAY_BOTTOM + 1)
        }
        occupied = set(snake.body)
        for item in self.items:
            occupied.add(item.pos)
        if obstacles:
            occupied |= obstacles
        return list(all_cells - occupied)

    def _pick_food_type(self) -> FoodConfig:
        types   = C.FOOD_TYPES
        weights = [ft.spawn_weight for ft in types]
        total   = sum(weights)
        roll    = random.random() * total
        cumulative = 0
        for ft, w in zip(types, weights):
            cumulative += w
            if roll < cumulative:
                return ft
        return types[0]

    def _try_spawn(self, snake: Snake, obstacles: set | None = None) -> bool:
        if len(self.items) >= C.MAX_FOOD_ON_SCREEN:
            return False
        free = self._free_cells(snake, obstacles)
        if not free:
            return False
        pos    = random.choice(free)
        config = self._pick_food_type()
        self.items.append(FoodItem(pos, config))
        return True

    def tick(self, dt_ms: float, snake: Snake,
             obstacles: set | None = None) -> None:
        for item in self.items:
            item.tick(dt_ms)
        self.items = [item for item in self.items if not item.expired]
        self._spawn_accum += dt_ms
        if self._spawn_accum >= C.FOOD_SPAWN_INTERVAL_MS:
            self._spawn_accum = 0.0
            self._try_spawn(snake, obstacles)

    def check_eat(self, snake: Snake,
                  obstacles: set | None = None) -> FoodItem | None:
        head = snake.head
        for item in self.items:
            if item.pos == head:
                self.items.remove(item)
                self._try_spawn(snake, obstacles)
                return item
        return None

    def ensure_food(self, snake: Snake,
                    obstacles: set | None = None) -> None:
        if not self.items:
            self._try_spawn(snake, obstacles)

    def clear_pos(self, pos: tuple) -> None:
        """Remove any food item at *pos* (called when obstacle spawns there)."""
        self.items = [i for i in self.items if i.pos != pos]


# ════════════════════════════════════════════════════════════════════════════
#  PowerUp  (NEW — TSIS 4)
# ════════════════════════════════════════════════════════════════════════════

class PowerUp:
    """A single power-up item sitting on the field."""
    def __init__(self, pos: tuple, config: PowerUpConfig):
        self.pos        = pos
        self.config     = config
        self.spawned_at = pygame.time.get_ticks()

    @property
    def expired(self) -> bool:
        return (pygame.time.get_ticks() - self.spawned_at) >= C.POWERUP_FIELD_MS

    @property
    def time_left_ms(self) -> int:
        elapsed = pygame.time.get_ticks() - self.spawned_at
        return max(0, C.POWERUP_FIELD_MS - elapsed)

    @property
    def lifetime_fraction(self) -> float:
        return self.time_left_ms / C.POWERUP_FIELD_MS


class PowerUpManager:
    """
    Manages the one power-up that can exist on the field at a time,
    plus any currently active effect after collection.

    Active-effect state
    -------------------
    active_config   : the PowerUpConfig in effect (or None)
    effect_end_ms   : pygame.time.get_ticks() value when the effect ends
    """

    def __init__(self):
        self.field_item  : PowerUp | None      = None
        self.active_config: PowerUpConfig | None = None
        self.effect_end_ms: int                 = 0
        self._next_spawn_ms: int                = self._random_next()

    @staticmethod
    def _random_next() -> int:
        """Return the ticks timestamp when the next power-up should try to spawn."""
        delay = random.randint(8_000, 18_000)   # 8–18 s between spawns
        return pygame.time.get_ticks() + delay

    def _free_cells(self, snake: Snake,
                    obstacles: set | None,
                    food_positions: set) -> list[tuple]:
        all_cells = {
            (c, r)
            for c in range(C.PLAY_LEFT, C.PLAY_RIGHT + 1)
            for r in range(C.PLAY_TOP,  C.PLAY_BOTTOM + 1)
        }
        occupied = set(snake.body) | food_positions
        if obstacles:
            occupied |= obstacles
        if self.field_item:
            occupied.add(self.field_item.pos)
        return list(all_cells - occupied)

    def update(self, snake: Snake,
               obstacles: set | None,
               food_positions: set) -> None:
        """Called once per game step to tick the field item and try spawning."""
        now = pygame.time.get_ticks()

        # Expire field item if timer ran out
        if self.field_item and self.field_item.expired:
            self.field_item = None

        # Expire active effect
        if self.active_config and now >= self.effect_end_ms:
            self.active_config = None

        # Try to spawn a new field item
        if self.field_item is None and now >= self._next_spawn_ms:
            free = self._free_cells(snake, obstacles, food_positions)
            if free:
                config = random.choice(C.ALL_POWERUPS)
                self.field_item = PowerUp(random.choice(free), config)
                self._next_spawn_ms = now + C.POWERUP_FIELD_MS + random.randint(5_000, 15_000)

    def check_collect(self, snake: Snake) -> PowerUpConfig | None:
        """
        Check whether the snake's head is on the field power-up.
        If so, consume it and activate the effect. Returns the config or None.
        """
        if self.field_item and snake.head == self.field_item.pos:
            config = self.field_item.config
            self.field_item   = None
            self.active_config = config
            self.effect_end_ms = pygame.time.get_ticks() + C.POWERUP_EFFECT_MS

            # Shield is special: flag the snake directly
            if config is C.POWERUP_SHIELD:
                snake.shield = True

            return config
        return None

    # ── Query helpers ─────────────────────────────────────────────────────────

    @property
    def has_speed_boost(self) -> bool:
        return self.active_config is C.POWERUP_SPEED_BOOST

    @property
    def has_slow_mo(self) -> bool:
        return self.active_config is C.POWERUP_SLOW_MO

    @property
    def effect_fraction(self) -> float:
        """Remaining effect lifetime as 0–1 fraction."""
        if not self.active_config:
            return 0.0
        remaining = self.effect_end_ms - pygame.time.get_ticks()
        return max(0.0, remaining / C.POWERUP_EFFECT_MS)

    @property
    def effect_remaining_s(self) -> float:
        if not self.active_config:
            return 0.0
        return max(0.0, (self.effect_end_ms - pygame.time.get_ticks()) / 1000.0)


# ════════════════════════════════════════════════════════════════════════════
#  ObstacleManager  (NEW — TSIS 4)
# ════════════════════════════════════════════════════════════════════════════

class ObstacleManager:
    """
    Places and stores static obstacle blocks inside the arena.

    Obstacles first appear at OBSTACLE_START_LEVEL.
    Each subsequent level adds OBSTACLE_PER_LEVEL more blocks.
    No block is placed within OBSTACLE_SAFETY_RADIUS cells of the
    snake's head at the moment obstacles are generated.
    """

    def __init__(self):
        self.blocks: set[tuple] = set()
        self._current_level = 0

    def update_for_level(self, level: int, snake: Snake,
                         food_positions: set) -> None:
        """
        Called whenever the level changes. Adds new blocks if needed.
        Safe — does not re-randomise existing blocks.
        """
        if level < C.OBSTACLE_START_LEVEL or level == self._current_level:
            return

        self._current_level = level

        # Number of blocks desired for this level
        extra_levels = level - C.OBSTACLE_START_LEVEL
        target = min(
            C.OBSTACLE_BASE_COUNT + extra_levels * C.OBSTACLE_PER_LEVEL,
            C.OBSTACLE_MAX,
        )
        to_add = max(0, target - len(self.blocks))
        if to_add == 0:
            return

        # Build candidate cells: exclude snake body, safety radius, existing
        # blocks, and food positions
        hx, hy = snake.head
        forbidden = set(snake.body) | self.blocks | food_positions
        for dc in range(-C.OBSTACLE_SAFETY_RADIUS, C.OBSTACLE_SAFETY_RADIUS + 1):
            for dr in range(-C.OBSTACLE_SAFETY_RADIUS, C.OBSTACLE_SAFETY_RADIUS + 1):
                forbidden.add((hx + dc, hy + dr))

        candidates = [
            (c, r)
            for c in range(C.PLAY_LEFT, C.PLAY_RIGHT + 1)
            for r in range(C.PLAY_TOP,  C.PLAY_BOTTOM + 1)
            if (c, r) not in forbidden
        ]
        random.shuffle(candidates)
        for cell in candidates[:to_add]:
            self.blocks.add(cell)

    def collides(self, cell: tuple) -> bool:
        return cell in self.blocks


# ════════════════════════════════════════════════════════════════════════════
#  LevelSystem
# ════════════════════════════════════════════════════════════════════════════

class LevelSystem:
    def __init__(self):
        self.score              = 0
        self.level              = 1
        self.foods_eaten        = 0
        self._foods_this_level  = 0
        self.speed              = C.SPEED_INIT
        self.level_up_flash     = 0
        self._base_speed        = C.SPEED_INIT   # speed without power-up mods

    def eat(self, food_item: FoodItem) -> bool:
        """
        Award score for a non-poison food item, check for level-up.
        Returns True if a level-up occurred.
        """
        pts = (C.POINTS_PER_FOOD
               * food_item.config.weight
               * (C.POINTS_LEVEL_MULT * self.level))
        self.score            += pts
        self.foods_eaten      += 1
        self._foods_this_level += 1

        if self._foods_this_level >= C.FOOD_PER_LEVEL:
            self._foods_this_level = 0
            self.level            += 1
            self._base_speed       = min(self._base_speed + C.SPEED_INCREMENT,
                                         C.SPEED_MAX)
            self.speed             = self._base_speed
            self.level_up_flash    = 45
            return True
        return False

    def apply_speed_modifier(self, powerup_mgr: 'PowerUpManager') -> None:
        """Recalculate speed taking the current power-up into account."""
        if powerup_mgr.has_speed_boost:
            self.speed = min(self._base_speed * C.POWERUP_SPEED_MULT, C.SPEED_MAX)
        elif powerup_mgr.has_slow_mo:
            self.speed = max(self._base_speed * C.POWERUP_SLOW_MULT, 1.0)
        else:
            self.speed = self._base_speed

    def tick_flash(self) -> None:
        if self.level_up_flash > 0:
            self.level_up_flash -= 1

    @property
    def move_interval_ms(self) -> float:
        return 1000.0 / self.speed
