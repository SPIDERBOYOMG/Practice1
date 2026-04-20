"""
settings.py
===========
Central config for the Snake game.
Change values here to tune gameplay without touching logic files.
"""

# ── Window & grid ────────────────────────────────────────────────────────────
TITLE       = "PIXEL SNAKE"
CELL        = 20          # size of one grid cell in pixels
COLS        = 25          # grid width  in cells  → window width  = 500 px
ROWS        = 25          # grid height in cells  → window height = 500 px
WIN_W       = COLS * CELL # 500
WIN_H       = ROWS * CELL # 500
HUD_H       = 48          # pixel height of the HUD bar above the grid
FPS_DISPLAY = 60          # pygame clock cap (does NOT affect snake speed)

# ── Border / wall ────────────────────────────────────────────────────────────
# The playfield is surrounded by a 1-cell thick wall.
# Snake body and food are only placed inside this border.
WALL_THICKNESS = 1        # cells

# Playfield inner bounds (inclusive cell indices)
PLAY_LEFT   = WALL_THICKNESS
PLAY_TOP    = WALL_THICKNESS
PLAY_RIGHT  = COLS - WALL_THICKNESS - 1   # = 23
PLAY_BOTTOM = ROWS - WALL_THICKNESS - 1   # = 23

# ── Starting snake ───────────────────────────────────────────────────────────
SNAKE_START_X   = COLS // 2   # 12  (grid column)
SNAKE_START_Y   = ROWS // 2   # 12  (grid row)
SNAKE_START_LEN = 3           # initial body length
SNAKE_START_DIR = (1, 0)      # moving right

# ── Level system ─────────────────────────────────────────────────────────────
# Speed is measured in "moves per second".
# Each level raises the speed by SPEED_INCREMENT.
SPEED_INIT      = 6.0    # moves/sec at level 1
SPEED_INCREMENT = 1.5    # added per level
SPEED_MAX       = 22.0   # hard cap
FOOD_PER_LEVEL  = 4      # foods eaten to advance one level

# ── Scoring ──────────────────────────────────────────────────────────────────
POINTS_PER_FOOD   = 10   # base points for eating food
POINTS_LEVEL_MULT = 1    # score multiplier = level (so level 3 → 30 pts)

# ── Palette  (retro pixel style) ─────────────────────────────────────────────
COL_BG          = (  8,  12,   8)    # very dark green-black background
COL_WALL        = ( 40,  80,  40)    # dim green wall blocks
COL_WALL_HL     = ( 60, 120,  60)    # wall highlight pixel (top-left of cell)
COL_GRID        = ( 14,  20,  14)    # faint grid lines inside play area
COL_SNAKE_HEAD  = ( 80, 255,  80)    # bright green head
COL_SNAKE_BODY  = ( 40, 180,  40)    # medium green body
COL_SNAKE_DARK  = ( 20,  90,  20)    # darker segment shade
COL_SNAKE_EYE   = (220, 255, 220)    # eye whites
COL_FOOD        = (255,  60,  60)    # red apple body
COL_FOOD_HL     = (255, 160, 100)    # apple highlight
COL_FOOD_STEM   = ( 80, 160,  40)    # apple stem
COL_HUD_BG      = (  5,   8,   5)    # HUD panel background
COL_HUD_BORDER  = ( 40,  80,  40)    # HUD bottom border line
COL_TEXT_SCORE  = (255, 220,  40)    # score text (yellow)
COL_TEXT_LEVEL  = (100, 220, 255)    # level text (cyan)
COL_TEXT_DIM    = (120, 160, 120)    # label text (dim green)
COL_GAMEOVER_BG = (  0,   0,   0)    # game-over overlay
COL_GAMEOVER_TXT= (220,  40,  40)    # "GAME OVER" text
COL_WHITE       = (255, 255, 255)
COL_LEVEL_UP    = (255, 220,  40)    # level-up flash colour
