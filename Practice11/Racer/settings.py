"""
settings.py
===========
Central configuration for PIXEL RACER.
All tweakable constants live here — nothing is magic-numbered in game code.

New in this version:
  • COIN_TYPES      — weighted coin table (rarity, value, visual style)
  • ENEMY_BOOST_*   — enemy speed-up system triggered by coins collected
"""

import os

# ── Window ───────────────────────────────────────────────────────────────────
TITLE      = "PIXEL RACER"
WIN_W      = 400        # window width  (px)
WIN_H      = 600        # window height (px)
FPS        = 60         # target frames-per-second

# ── Road geometry ─────────────────────────────────────────────────────────────
ROAD_LEFT  = 72                      # x where asphalt starts (after left kerb)
ROAD_RIGHT = WIN_W - 72              # x where asphalt ends
ROAD_W     = ROAD_RIGHT - ROAD_LEFT  # total driveable width (256 px)
LANE_W     = ROAD_W // 3             # 3 lanes, each ~85 px wide

# Lane centre x-coordinates (used by spawners to snap objects to lanes)
LANES      = [ROAD_LEFT + LANE_W // 2 + i * LANE_W for i in range(3)]

# ── Scrolling ─────────────────────────────────────────────────────────────────
SCROLL_SPEED_INIT = 5      # road scroll speed at game start (px/frame)
SCROLL_SPEED_MAX  = 18     # absolute maximum scroll speed
SPEED_INCREMENT   = 0.002  # scroll speed growth per frame (passive ramp)

# ── Player ────────────────────────────────────────────────────────────────────
PLAYER_SPEED   = 5          # horizontal movement speed (px/frame)
PLAYER_START_X = LANES[1]   # start in the middle lane
PLAYER_START_Y = WIN_H - 100

# ── Enemy cars ────────────────────────────────────────────────────────────────
ENEMY_SPAWN_DELAY  = 80   # frames between enemy spawns (initial value)

# Base extra speed enemies have over the road scroll.
# This value is INCREASED every time an enemy-boost threshold is crossed.
ENEMY_SPEED_EXTRA      = 2    # initial extra speed (px/frame)
ENEMY_SPEED_EXTRA_MAX  = 12   # hard cap so the game stays playable

# ── Enemy speed-boost system ─────────────────────────────────────────────────
# Every time the player collects ENEMY_BOOST_EVERY_N coins (by count, not value)
# enemy cars gain ENEMY_BOOST_AMOUNT extra px/frame of speed.
# A "DANGER!" warning banner flashes on-screen for ENEMY_BOOST_FLASH_FRAMES frames.
ENEMY_BOOST_EVERY_N      = 5    # coins collected between each boost
ENEMY_BOOST_AMOUNT       = 0.8  # extra px/frame added to enemy speed per boost
ENEMY_BOOST_FLASH_FRAMES = 90   # how long the warning banner stays visible (~1.5 s)

# ── Coin system ───────────────────────────────────────────────────────────────
# Maximum number of coins visible on the road at once (all types combined)
COIN_MAX_ON_ROAD  = 5

# Probability per frame that the game ATTEMPTS to spawn a coin.
# The actual type chosen is then weighted by COIN_TYPES below.
COIN_SPAWN_CHANCE = 0.009

# Coins scroll slightly slower than the road so the player has reaction time
COIN_SPEED_FACTOR = 0.8

# ── Weighted coin type table ──────────────────────────────────────────────────
# Each entry defines one coin rarity tier.
#
# Keys:
#   name          – identifier string (used for debug / HUD labels)
#   weight        – relative spawn probability (higher = more common)
#                   Weights are summed and a weighted-random pick is made.
#   value         – score points awarded when this coin is collected
#   color         – (R, G, B) base colour used to draw the coin sprite
#   highlight     – (R, G, B) inner shine colour
#   outline       – (R, G, B) border / shadow colour
#   radius_factor – visual size multiplier relative to base coin size (1.0)
#   label_color   – (R, G, B) used in the HUD last-pickup indicator
#
# Total weight = 60+25+12+3 = 100 (convenient but not required to sum to 100).
COIN_TYPES = [
    {
        "name":          "bronze",
        "weight":        60,          # common  — appears most often
        "value":         1,
        "color":         (190,  95,  30),
        "highlight":     (230, 160,  80),
        "outline":       ( 90,  40,  10),
        "radius_factor": 0.85,
        "label_color":   (220, 140,  60),
    },
    {
        "name":          "silver",
        "weight":        25,          # uncommon
        "value":         3,
        "color":         (170, 175, 185),
        "highlight":     (230, 235, 245),
        "outline":       ( 80,  85,  95),
        "radius_factor": 1.0,
        "label_color":   (210, 215, 225),
    },
    {
        "name":          "gold",
        "weight":        12,          # rare
        "value":         5,
        "color":         (255, 200,   0),
        "highlight":     (255, 245, 140),
        "outline":       (140,  90,   0),
        "radius_factor": 1.15,
        "label_color":   (255, 220,  40),
    },
    {
        "name":          "gem",
        "weight":        3,           # very rare — cyan diamond
        "value":         10,
        "color":         ( 60, 220, 255),
        "highlight":     (200, 250, 255),
        "outline":       ( 20,  80, 120),
        "radius_factor": 1.3,
        "label_color":   (100, 240, 255),
    },
]

# ── Explosion animation ───────────────────────────────────────────────────────
EXPLOSION_FRAME_DUR = 6   # display frames per explosion sprite frame

# ── HUD ───────────────────────────────────────────────────────────────────────
HUD_MARGIN = 8   # px gap from screen edges

# ── Retro colour palette ──────────────────────────────────────────────────────
COL_BG          = ( 15,  15,  20)   # dark background behind the road
COL_HUD_TEXT    = (255, 220,  40)   # yellow HUD label text
COL_SCORE_TEXT  = (255, 255, 255)   # white score digits
COL_COIN_TEXT   = (255, 220,   0)   # gold coin-count text
COL_GAME_OVER   = (220,  40,  40)   # red "GAME OVER" text
COL_WHITE       = (255, 255, 255)
COL_DANGER      = (255,  60,  40)   # "DANGER!" warning colour
COL_DANGER_DIM  = (180,  40,  20)   # secondary danger colour

# ── File paths ────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def asset(name: str) -> str:
    """Return the full filesystem path for an asset file by name."""
    return os.path.join(ASSETS_DIR, name)
