"""
settings.py
===========
Central configuration for PIXEL RACER – TSIS-3 Edition.
All tweakable constants live here.  User preferences (sound, car colour,
difficulty) are stored in settings.json via persistence.py.
"""

import os

# ── Window ────────────────────────────────────────────────────────────────────
TITLE   = "PIXEL RACER – TSIS 3"
WIN_W   = 400
WIN_H   = 600
FPS     = 60

# ── Road geometry ─────────────────────────────────────────────────────────────
ROAD_LEFT  = 72
ROAD_RIGHT = WIN_W - 72
ROAD_W     = ROAD_RIGHT - ROAD_LEFT
LANE_W     = ROAD_W // 3
LANES      = [ROAD_LEFT + LANE_W // 2 + i * LANE_W for i in range(3)]

# ── Scrolling ─────────────────────────────────────────────────────────────────
SCROLL_SPEED_INIT = 5
SCROLL_SPEED_MAX  = 20
SPEED_INCREMENT   = 0.002

# ── Player ────────────────────────────────────────────────────────────────────
PLAYER_SPEED   = 5
PLAYER_START_X = LANES[1]
PLAYER_START_Y = WIN_H - 100

# ── Enemy / traffic cars ──────────────────────────────────────────────────────
ENEMY_SPAWN_DELAY      = 80
ENEMY_SPEED_EXTRA      = 2
ENEMY_SPEED_EXTRA_MAX  = 14
ENEMY_BOOST_EVERY_N    = 5
ENEMY_BOOST_AMOUNT     = 0.8
ENEMY_BOOST_FLASH_FRAMES = 90

# ── Coin system ───────────────────────────────────────────────────────────────
COIN_MAX_ON_ROAD  = 5
COIN_SPAWN_CHANCE = 0.009
COIN_SPEED_FACTOR = 0.8

COIN_TYPES = [
    {
        "name": "bronze", "weight": 60, "value": 1,
        "color": (190, 95, 30), "highlight": (230, 160, 80),
        "outline": (90, 40, 10), "radius_factor": 0.85,
        "label_color": (220, 140, 60),
    },
    {
        "name": "silver", "weight": 25, "value": 3,
        "color": (170, 175, 185), "highlight": (230, 235, 245),
        "outline": (80, 85, 95), "radius_factor": 1.0,
        "label_color": (210, 215, 225),
    },
    {
        "name": "gold", "weight": 12, "value": 5,
        "color": (255, 200, 0), "highlight": (255, 245, 140),
        "outline": (140, 90, 0), "radius_factor": 1.15,
        "label_color": (255, 220, 40),
    },
    {
        "name": "gem", "weight": 3, "value": 10,
        "color": (60, 220, 255), "highlight": (200, 250, 255),
        "outline": (20, 80, 120), "radius_factor": 1.3,
        "label_color": (100, 240, 255),
    },
]

# ── Explosion ──────────────────────────────────────────────────────────────────
EXPLOSION_FRAME_DUR = 6

# ── HUD ───────────────────────────────────────────────────────────────────────
HUD_MARGIN = 8

# ── Colour palette ────────────────────────────────────────────────────────────
COL_BG          = (15,  15,  20)
COL_HUD_TEXT    = (255, 220, 40)
COL_SCORE_TEXT  = (255, 255, 255)
COL_COIN_TEXT   = (255, 220,  0)
COL_GAME_OVER   = (220,  40, 40)
COL_WHITE       = (255, 255, 255)
COL_DANGER      = (255,  60, 40)
COL_DANGER_DIM  = (180,  40, 20)

# ── Car colour tints ──────────────────────────────────────────────────────────
CAR_COLOR_TINTS = {
    "red":    (255, 80,  80,  255),
    "blue":   (80,  120, 255, 255),
    "green":  (80,  220, 100, 255),
    "yellow": (255, 230, 60,  255),
    "purple": (180, 80,  240, 255),
}

# ── Difficulty presets ─────────────────────────────────────────────────────────
DIFFICULTY_PRESETS = {
    "easy": {
        "enemy_spawn_delay":    120,
        "obstacle_chance":      0.003,
        "speed_increment":      0.001,
        "scroll_speed_init":    4,
        "powerup_spawn_chance": 0.008,
        "traffic_extra_mult":   0.7,
    },
    "normal": {
        "enemy_spawn_delay":    80,
        "obstacle_chance":      0.006,
        "speed_increment":      0.002,
        "scroll_speed_init":    5,
        "powerup_spawn_chance": 0.005,
        "traffic_extra_mult":   1.0,
    },
    "hard": {
        "enemy_spawn_delay":    45,
        "obstacle_chance":      0.013,
        "speed_increment":      0.004,
        "scroll_speed_init":    7,
        "powerup_spawn_chance": 0.003,
        "traffic_extra_mult":   1.4,
    },
}

# ── Power-up system ────────────────────────────────────────────────────────────
POWERUP_MAX_ON_ROAD  = 2
POWERUP_LIFETIME_S   = 8.0      # seconds before a power-up disappears
POWERUP_SPEED_FACTOR = 0.75     # scroll factor (slightly slower than coins)

POWERUP_TYPES = [
    {
        "name":     "nitro",
        "label":    "NITRO",
        "duration": 4.0,         # seconds active
        "color":    (255, 200,  0),
        "icon_col": (255, 240, 80),
        "symbol":   "⚡",
        "desc":     "Speed boost!",
    },
    {
        "name":     "shield",
        "label":    "SHIELD",
        "duration": None,        # until hit
        "color":    (60,  160, 255),
        "icon_col": (160, 220, 255),
        "symbol":   "🛡",
        "desc":     "One free hit!",
    },
    {
        "name":     "repair",
        "label":    "REPAIR",
        "duration": 0,           # instant
        "color":    (80,  220, 100),
        "icon_col": (160, 255, 180),
        "symbol":   "🔧",
        "desc":     "Cleared!",
    },
]

# ── Obstacle types ─────────────────────────────────────────────────────────────
OBSTACLE_MAX_ON_ROAD = 4
OBSTACLE_SPEED_FACTOR = 0.9

OBSTACLE_TYPES = [
    {
        "name":   "pothole",
        "color":  (20,  20,  25),
        "border": (60,  60,  70),
        "w": 28, "h": 18,
        "lethal": True,          # causes crash (unless shielded)
        "slow":   False,
    },
    {
        "name":   "oil_spill",
        "color":  (15,  15,  40),
        "border": (40,  40,  80),
        "w": 38, "h": 22,
        "lethal": False,
        "slow":   True,          # temporarily slows player
    },
    {
        "name":   "barrier",
        "color":  (240, 130,  20),
        "border": (180,  80,  10),
        "w": 34, "h": 14,
        "lethal": True,
        "slow":   False,
    },
]

# ── Nitro strip (road event) ───────────────────────────────────────────────────
NITRO_STRIP_CHANCE      = 0.0008   # per frame
NITRO_STRIP_SPEED_BONUS = 4        # added to scroll speed
NITRO_STRIP_DURATION    = 2.0      # seconds

# ── Distance / race ────────────────────────────────────────────────────────────
RACE_DISTANCE_M  = 5000    # total race length in metres
PX_PER_METRE     = 40.0    # pixels scrolled = 1 metre at base speed

# ── Score multipliers ──────────────────────────────────────────────────────────
SCORE_PER_FRAME  = 1
SCORE_PER_METRE  = 2
NITRO_SCORE_BONUS   = 50
SHIELD_SCORE_BONUS  = 100
REPAIR_SCORE_BONUS  = 75

# ── Slow penalty ─────────────────────────────────────────────────────────────-
OIL_SLOW_FACTOR   = 0.45   # player speed multiplied by this during oil effect
OIL_SLOW_DURATION = 2.5    # seconds

# ── File paths ────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def asset(name: str) -> str:
    return os.path.join(ASSETS_DIR, name)
