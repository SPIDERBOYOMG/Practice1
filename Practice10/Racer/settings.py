"""
settings.py
===========
Central configuration file for the Racer game.
All tweakable constants live here so nothing is "magic-numbered" in game code.
"""

import os

# ── Window ──────────────────────────────────────────────────────────────────
TITLE       = "PIXEL RACER"
WIN_W       = 400          # window width  (px)
WIN_H       = 600          # window height (px)
FPS         = 60           # target frames-per-second

# ── Road geometry ───────────────────────────────────────────────────────────
ROAD_LEFT   = 72           # x where asphalt starts (after left kerb)
ROAD_RIGHT  = WIN_W - 72   # x where asphalt ends
ROAD_W      = ROAD_RIGHT - ROAD_LEFT   # total driveable width (256 px)
LANE_W      = ROAD_W // 3             # 3 lanes, each 85 px wide
# Lane centre x-coordinates
LANES       = [ROAD_LEFT + LANE_W // 2 + i * LANE_W for i in range(3)]

# ── Scrolling ───────────────────────────────────────────────────────────────
SCROLL_SPEED_INIT  = 5     # road scroll speed at game start (px/frame)
SCROLL_SPEED_MAX   = 18    # maximum scroll speed
SPEED_INCREMENT    = 0.002 # how much scroll speed grows each frame

# ── Player ──────────────────────────────────────────────────────────────────
PLAYER_SPEED    = 5        # horizontal movement speed (px/frame)
PLAYER_START_X  = LANES[1] # start in the middle lane (centre-aligned below)
PLAYER_START_Y  = WIN_H - 100

# ── Enemy cars ──────────────────────────────────────────────────────────────
ENEMY_SPAWN_DELAY  = 80    # frames between enemy spawns (initial)
ENEMY_SPEED_EXTRA  = 2     # enemies move faster than road scroll by this much

# ── Coins ───────────────────────────────────────────────────────────────────
COIN_SPAWN_CHANCE  = 0.008 # probability per frame that a new coin spawns (0-1)
COIN_MAX_ON_ROAD   = 5     # never more than this many coins visible at once
COIN_SPEED_FACTOR  = 0.8   # coins scroll slightly slower than road (float)

# ── Explosion animation ──────────────────────────────────────────────────────
EXPLOSION_FRAME_DUR = 6    # frames each explosion sprite is shown

# ── HUD ──────────────────────────────────────────────────────────────────────
HUD_FONT_SIZE   = 16       # pixel font size for score / coins
HUD_MARGIN      = 8        # px from screen edges

# ── Palette (retro) ──────────────────────────────────────────────────────────
COL_BG          = ( 15,  15,  20)   # very dark background (behind road)
COL_HUD_BG      = (  0,   0,   0, 160)  # semi-transparent HUD panel
COL_HUD_TEXT    = (255, 220,  40)   # yellow retro HUD text
COL_SCORE_TEXT  = (255, 255, 255)
COL_COIN_TEXT   = (255, 220,   0)
COL_GAME_OVER   = (220,  40,  40)
COL_WHITE       = (255, 255, 255)

# ── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(__file__)
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")

def asset(name: str) -> str:
    """Return full path for an asset file."""
    return os.path.join(ASSETS_DIR, name)
