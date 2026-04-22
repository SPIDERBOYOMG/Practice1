"""
settings.py
===========
Central configuration for the Snake game.
All tuneable values live here so game-logic files never contain magic numbers.

New in Practice 8 extension
----------------------------
  - FOOD_TYPES          : list of FoodConfig dicts describing each food variety
  - MAX_FOOD_ON_SCREEN  : how many food items may coexist on the grid
  - FOOD_SPAWN_INTERVAL : ms between automatic new-food spawns
  - Colour tokens for each food type and the timer ring
"""

from dataclasses import dataclass


# ── Window & grid ─────────────────────────────────────────────────────────────
TITLE       = "PIXEL SNAKE"
CELL        = 20          # size of one grid cell in pixels
COLS        = 25          # grid width  in cells  → window width  = 500 px
ROWS        = 25          # grid height in cells  → window height = 500 px
WIN_W       = COLS * CELL # 500 px
WIN_H       = ROWS * CELL # 500 px
HUD_H       = 48          # pixel height of the HUD bar below the grid
FPS_DISPLAY = 60          # pygame clock cap  (does NOT affect snake speed)

# ── Border / wall ─────────────────────────────────────────────────────────────
# The playfield is surrounded by a 1-cell thick wall.
# Snake body and food are only ever placed inside this border.
WALL_THICKNESS = 1

# Playfield inner bounds (inclusive cell indices)
PLAY_LEFT   = WALL_THICKNESS
PLAY_TOP    = WALL_THICKNESS
PLAY_RIGHT  = COLS - WALL_THICKNESS - 1   # = 23
PLAY_BOTTOM = ROWS - WALL_THICKNESS - 1   # = 23

# ── Starting snake ────────────────────────────────────────────────────────────
SNAKE_START_X   = COLS // 2   # 12
SNAKE_START_Y   = ROWS // 2   # 12
SNAKE_START_LEN = 3
SNAKE_START_DIR = (1, 0)      # moving right

# ── Level / speed ─────────────────────────────────────────────────────────────
SPEED_INIT      = 6.0    # moves per second at level 1
SPEED_INCREMENT = 1.5    # speed added per level-up
SPEED_MAX       = 22.0   # hard cap
FOOD_PER_LEVEL  = 4      # apples needed to advance one level

# ── Scoring ───────────────────────────────────────────────────────────────────
POINTS_PER_FOOD   = 10   # base points — multiplied by food weight × level
POINTS_LEVEL_MULT = 1    # additional level multiplier

# ════════════════════════════════════════════════════════════════════════════
#  Food system  (NEW in Practice 8)
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class FoodConfig:
    """
    Describes one variety of food.

    Attributes
    ----------
    name          : display name shown in the HUD (e.g. "APPLE")
    weight        : score multiplier applied on top of base points × level.
                    An apple (weight=1) at level 2 gives  10 × 1 × 2 = 20 pts.
                    A cherry (weight=3) at level 2 gives  10 × 3 × 2 = 60 pts.
    lifetime_s    : seconds this food item stays visible before disappearing.
                    Set to float('inf') to make a food type permanent.
    spawn_weight  : relative probability used by weighted-random selection.
                    E.g. apple=50, cherry=25, golden=10 means apple is 5× more
                    likely to spawn than golden.
    col_body      : main fill colour (RGB tuple)
    col_highlight : small highlight spot colour
    col_stem      : stem / leaf colour
    col_timer     : colour of the countdown ring drawn around the item
    """
    name        : str
    weight      : int
    lifetime_s  : float
    spawn_weight: int
    col_body    : tuple
    col_highlight: tuple
    col_stem    : tuple
    col_timer   : tuple


# Each entry here automatically becomes an option in FoodManager's spawner.
# Add or remove rows freely — the rest of the code adapts automatically.
FOOD_TYPES: list[FoodConfig] = [
    FoodConfig(
        name         = "APPLE",
        weight       = 1,           # base score — most common, least valuable
        lifetime_s   = 20.0,        # 20 seconds before disappearing
        spawn_weight = 50,          # ~56 % of all spawns
        col_body     = (220,  50,  50),
        col_highlight= (255, 160, 100),
        col_stem     = ( 80, 160,  40),
        col_timer    = (100, 220, 100),   # green ring
    ),
    FoodConfig(
        name         = "CHERRY",
        weight       = 3,           # 3× score — moderately common, valuable
        lifetime_s   = 12.0,        # shorter window: 12 seconds
        spawn_weight = 30,          # ~33 % of all spawns
        col_body     = (200,  20, 100),
        col_highlight= (255, 100, 160),
        col_stem     = ( 60, 140,  30),
        col_timer    = (255, 180,  50),   # amber ring
    ),
    FoodConfig(
        name         = "GOLDEN",
        weight       = 8,           # 8× score — rare, very valuable
        lifetime_s   = 7.0,         # shortest window: only 7 seconds!
        spawn_weight = 10,          # ~11 % of all spawns
        col_body     = (255, 210,   0),
        col_highlight= (255, 255, 160),
        col_stem     = (180, 130,   0),
        col_timer    = (255, 220,   0),   # gold ring
    ),
]

# Maximum number of food items that may exist simultaneously on the grid.
# When fewer than this many items are present, the spawner may add more.
MAX_FOOD_ON_SCREEN: int = 3

# Milliseconds between automatic new-food spawn attempts.
# The spawner only places a new item if the current count < MAX_FOOD_ON_SCREEN.
FOOD_SPAWN_INTERVAL_MS: int = 4_000   # 4 seconds

# Threshold (fraction of lifetime remaining) below which food starts blinking
# to alert the player it is about to disappear.
FOOD_BLINK_THRESHOLD: float = 0.25   # bottom 25 % of lifetime → blink


# ── Palette (retro pixel style) ───────────────────────────────────────────────
COL_BG          = (  8,  12,   8)
COL_WALL        = ( 40,  80,  40)
COL_WALL_HL     = ( 60, 120,  60)
COL_GRID        = ( 14,  20,  14)
COL_SNAKE_HEAD  = ( 80, 255,  80)
COL_SNAKE_BODY  = ( 40, 180,  40)
COL_SNAKE_DARK  = ( 20,  90,  20)
COL_SNAKE_EYE   = (220, 255, 220)
COL_HUD_BG      = (  5,   8,   5)
COL_HUD_BORDER  = ( 40,  80,  40)
COL_TEXT_SCORE  = (255, 220,  40)
COL_TEXT_LEVEL  = (100, 220, 255)
COL_TEXT_DIM    = (120, 160, 120)
COL_GAMEOVER_BG = (  0,   0,   0)
COL_GAMEOVER_TXT= (220,  40,  40)
COL_WHITE       = (255, 255, 255)
COL_LEVEL_UP    = (255, 220,  40)

# Legacy alias — kept for any renderer code that still references COL_FOOD
COL_FOOD        = FOOD_TYPES[0].col_body
COL_FOOD_HL     = FOOD_TYPES[0].col_highlight
COL_FOOD_STEM   = FOOD_TYPES[0].col_stem
