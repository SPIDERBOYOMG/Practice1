"""
config.py
=========
Central configuration for the Snake game — TSIS 4 edition.
All tuneable values live here so game-logic files never contain magic numbers.

New in TSIS 4
-------------
  - POISON food type
  - POWER_UP constants
  - OBSTACLE constants
  - Screen / UI constants
  - DB connection defaults
"""

from dataclasses import dataclass


# ── Window & grid ─────────────────────────────────────────────────────────────
TITLE       = "PIXEL SNAKE  ·  TSIS 4"
CELL        = 20          # size of one grid cell in pixels
COLS        = 25          # grid width  in cells  → 500 px
ROWS        = 25          # grid height in cells  → 500 px
WIN_W       = COLS * CELL # 500 px
WIN_H       = ROWS * CELL # 500 px
HUD_H       = 48          # pixel height of HUD bar below the grid
TOTAL_H     = WIN_H + HUD_H
FPS_DISPLAY = 60

# ── Border / wall ─────────────────────────────────────────────────────────────
WALL_THICKNESS = 1
PLAY_LEFT   = WALL_THICKNESS
PLAY_TOP    = WALL_THICKNESS
PLAY_RIGHT  = COLS - WALL_THICKNESS - 1   # 23
PLAY_BOTTOM = ROWS - WALL_THICKNESS - 1   # 23

# ── Starting snake ────────────────────────────────────────────────────────────
SNAKE_START_X   = COLS // 2
SNAKE_START_Y   = ROWS // 2
SNAKE_START_LEN = 3
SNAKE_START_DIR = (1, 0)     # moving right

# ── Level / speed ─────────────────────────────────────────────────────────────
SPEED_INIT      = 6.0    # moves/s at level 1
SPEED_INCREMENT = 1.5
SPEED_MAX       = 22.0
FOOD_PER_LEVEL  = 4

# ── Scoring ───────────────────────────────────────────────────────────────────
POINTS_PER_FOOD   = 10
POINTS_LEVEL_MULT = 1

# ════════════════════════════════════════════════════════════════════════════
#  Food system
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class FoodConfig:
    name         : str
    weight       : int
    lifetime_s   : float
    spawn_weight : int
    col_body     : tuple
    col_highlight: tuple
    col_stem     : tuple
    col_timer    : tuple
    is_poison    : bool = False   # NEW: poison flag


FOOD_TYPES: list = [
    FoodConfig(
        name="APPLE", weight=1, lifetime_s=20.0, spawn_weight=50,
        col_body=(220, 50, 50), col_highlight=(255, 160, 100),
        col_stem=(80, 160, 40), col_timer=(100, 220, 100),
    ),
    FoodConfig(
        name="CHERRY", weight=3, lifetime_s=12.0, spawn_weight=30,
        col_body=(200, 20, 100), col_highlight=(255, 100, 160),
        col_stem=(60, 140, 30), col_timer=(255, 180, 50),
    ),
    FoodConfig(
        name="GOLDEN", weight=8, lifetime_s=7.0, spawn_weight=10,
        col_body=(255, 210, 0), col_highlight=(255, 255, 160),
        col_stem=(180, 130, 0), col_timer=(255, 220, 0),
    ),
    FoodConfig(                               # NEW — TSIS 4
        name="POISON", weight=0, lifetime_s=10.0, spawn_weight=15,
        col_body=(100, 0, 30), col_highlight=(180, 40, 80),
        col_stem=(60, 0, 20), col_timer=(200, 50, 50),
        is_poison=True,
    ),
]

MAX_FOOD_ON_SCREEN   : int   = 3
FOOD_SPAWN_INTERVAL_MS: int  = 4_000
FOOD_BLINK_THRESHOLD : float = 0.25

POISON_SHORTEN = 2   # segments removed when poison eaten

# ════════════════════════════════════════════════════════════════════════════
#  Power-ups  (NEW — TSIS 4)
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class PowerUpConfig:
    name      : str
    col_body  : tuple
    col_glow  : tuple
    symbol    : str      # single character drawn on the cell


POWERUP_SPEED_BOOST = PowerUpConfig(
    name="SPEED BOOST", col_body=(255, 200, 0), col_glow=(255, 255, 100),
    symbol="»",
)
POWERUP_SLOW_MO = PowerUpConfig(
    name="SLOW MO", col_body=(80, 160, 255), col_glow=(160, 220, 255),
    symbol="«",
)
POWERUP_SHIELD = PowerUpConfig(
    name="SHIELD", col_body=(160, 255, 160), col_glow=(200, 255, 200),
    symbol="★",
)

ALL_POWERUPS = [POWERUP_SPEED_BOOST, POWERUP_SLOW_MO, POWERUP_SHIELD]

POWERUP_EFFECT_MS   = 5_000   # how long effect lasts after collection (ms)
POWERUP_FIELD_MS    = 8_000   # how long power-up sits on field before vanishing (ms)
POWERUP_SPEED_MULT  = 1.7     # speed boost multiplier
POWERUP_SLOW_MULT   = 0.5     # slow-motion multiplier

# ════════════════════════════════════════════════════════════════════════════
#  Obstacles  (NEW — TSIS 4)
# ════════════════════════════════════════════════════════════════════════════

OBSTACLE_START_LEVEL   = 3    # obstacles first appear at this level
OBSTACLE_BASE_COUNT    = 4    # wall blocks added at level 3
OBSTACLE_PER_LEVEL     = 2    # extra blocks added per level beyond 3
OBSTACLE_MAX           = 20   # hard cap
OBSTACLE_SAFETY_RADIUS = 3    # clear cells around snake head at spawn

# ════════════════════════════════════════════════════════════════════════════
#  Palette
# ════════════════════════════════════════════════════════════════════════════
COL_BG           = (  8,  12,   8)
COL_WALL         = ( 40,  80,  40)
COL_WALL_HL      = ( 60, 120,  60)
COL_GRID         = ( 14,  20,  14)
COL_SNAKE_HEAD   = ( 80, 255,  80)
COL_SNAKE_BODY   = ( 40, 180,  40)
COL_SNAKE_DARK   = ( 20,  90,  20)
COL_SNAKE_EYE    = (220, 255, 220)
COL_HUD_BG       = (  5,   8,   5)
COL_HUD_BORDER   = ( 40,  80,  40)
COL_TEXT_SCORE   = (255, 220,  40)
COL_TEXT_LEVEL   = (100, 220, 255)
COL_TEXT_DIM     = (120, 160, 120)
COL_GAMEOVER_BG  = (  0,   0,   0)
COL_GAMEOVER_TXT = (220,  40,  40)
COL_WHITE        = (255, 255, 255)
COL_LEVEL_UP     = (255, 220,  40)
COL_OBSTACLE     = ( 80,  80, 100)
COL_OBSTACLE_HL  = (120, 120, 160)
COL_MENU_BG      = (  5,   8,   5)
COL_MENU_BTN     = ( 20,  60,  20)
COL_MENU_BTN_SEL = ( 40, 160,  40)
COL_MENU_BTN_TXT = (200, 255, 200)
COL_PERSONAL_BEST= (255, 180,  50)
COL_SHIELD_ACTIVE= (100, 255, 150)

COL_FOOD    = FOOD_TYPES[0].col_body
COL_FOOD_HL = FOOD_TYPES[0].col_highlight
COL_FOOD_STEM = FOOD_TYPES[0].col_stem

# ════════════════════════════════════════════════════════════════════════════
#  Database defaults
# ════════════════════════════════════════════════════════════════════════════
try:
    from secrets import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
except (ImportError, ModuleNotFoundError):
    DB_HOST = "localhost"
    DB_PORT = 5433
    DB_NAME = "snake_game"
    DB_USER = "postgres"
    DB_PASS = "postgres"
