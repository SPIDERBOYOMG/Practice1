"""
generate_assets.py
==================
Generates all pixel-art sprites for the Racer game.
Run ONCE before launching the game:
    python generate_assets.py
Produces PNG files inside the ./assets/ folder.
"""

import pygame
import os

# ── Output directory ────────────────────────────────────────────────────────
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

pygame.init()
# Dummy display needed by pygame.image.save
_screen = pygame.display.set_mode((1, 1), pygame.NOFRAME)


# ── Helper: save a surface ──────────────────────────────────────────────────
def save(surf: pygame.Surface, name: str) -> None:
    path = os.path.join(ASSETS_DIR, name)
    pygame.image.save(surf, path)
    print(f"  saved → {path}")


# ── Pixel grid helper ───────────────────────────────────────────────────────
def blit_pixels(surf: pygame.Surface, pixels: list[tuple], color) -> None:
    """Fill a list of (col, row) pixel positions with 'color'."""
    for col, row in pixels:
        surf.set_at((col, row), color)


# ═══════════════════════════════════════════════════════════════════════════
#  PLAYER CAR  (32 × 64 px, pixel retro style, blue)
# ═══════════════════════════════════════════════════════════════════════════
def make_player_car() -> pygame.Surface:
    W, H = 32, 64
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    s.fill((0, 0, 0, 0))

    BODY   = (30, 100, 220)    # blue body
    DARK   = (10,  50, 140)    # shading
    LIGHT  = (80, 160, 255)    # highlight
    WINDOW = (160, 220, 255)   # windshield
    WIN_D  = ( 60, 120, 180)   # window shadow
    WHEEL  = ( 20,  20,  20)   # tyre
    RIM    = (200, 200, 200)   # rim
    LIGHT_F= (255, 255, 180)   # headlight
    LIGHT_R= (220,  50,  50)   # taillight

    # ── Body silhouette
    body_cols = range(4, 28)
    for y in range(8, 56):
        for x in body_cols:
            s.set_at((x, y), BODY)
    # Rounded nose
    for x in range(6, 26):
        s.set_at((x, 6), BODY)
        s.set_at((x, 7), BODY)
    for x in range(8, 24):
        s.set_at((x, 5), BODY)

    # ── Rounded tail
    for x in range(6, 26):
        s.set_at((x, 56), BODY)
        s.set_at((x, 57), BODY)
    for x in range(8, 24):
        s.set_at((x, 58), BODY)

    # ── Dark shading (left side)
    for y in range(10, 54):
        for x in range(4, 8):
            s.set_at((x, y), DARK)

    # ── Highlight (right side stripe)
    for y in range(10, 54):
        s.set_at((25, y), LIGHT)

    # ── Windshield (front)
    for y in range(10, 22):
        for x in range(8, 24):
            s.set_at((x, y), WINDOW)
    for y in range(10, 22):
        for x in range(8, 12):
            s.set_at((x, y), WIN_D)

    # ── Rear window
    for y in range(42, 52):
        for x in range(8, 24):
            s.set_at((x, y), WINDOW)
    for y in range(42, 52):
        for x in range(8, 11):
            s.set_at((x, y), WIN_D)

    # ── Headlights (top)
    for x in range(8, 14):
        for y in range(5, 8):
            s.set_at((x, y), LIGHT_F)
    for x in range(18, 24):
        for y in range(5, 8):
            s.set_at((x, y), LIGHT_F)

    # ── Taillights (bottom)
    for x in range(8, 14):
        for y in range(57, 60):
            s.set_at((x, y), LIGHT_R)
    for x in range(18, 24):
        for y in range(57, 60):
            s.set_at((x, y), LIGHT_R)

    # ── Wheels (4 corners, drawn as dark blobs)
    def draw_wheel(cx, cy):
        for dx in range(-4, 5):
            for dy in range(-5, 6):
                if abs(dx) + abs(dy) < 8:
                    s.set_at((cx + dx, cy + dy), WHEEL)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                s.set_at((cx + dx, cy + dy), RIM)

    draw_wheel(3,  14)   # front-left
    draw_wheel(28, 14)   # front-right
    draw_wheel(3,  50)   # rear-left
    draw_wheel(28, 50)   # rear-right

    return s


# ═══════════════════════════════════════════════════════════════════════════
#  ENEMY CAR  (32 × 64 px, red)
# ═══════════════════════════════════════════════════════════════════════════
def make_enemy_car() -> pygame.Surface:
    W, H = 32, 64
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    s.fill((0, 0, 0, 0))

    BODY   = (200,  30,  30)
    DARK   = (110,  10,  10)
    LIGHT  = (255, 100,  80)
    WINDOW = (160, 220, 255)
    WIN_D  = ( 60, 120, 180)
    WHEEL  = ( 20,  20,  20)
    RIM    = (180, 180, 180)
    LIGHT_F= (255, 255, 180)
    LIGHT_R= (255, 140,  50)

    for y in range(8, 56):
        for x in range(4, 28):
            s.set_at((x, y), BODY)
    for x in range(6, 26):
        for y in [6, 7, 56, 57]:
            s.set_at((x, y), BODY)
    for x in range(8, 24):
        for y in [5, 58]:
            s.set_at((x, y), BODY)
    for y in range(10, 54):
        for x in range(4, 8):
            s.set_at((x, y), DARK)
    for y in range(10, 54):
        s.set_at((25, y), LIGHT)
    for y in range(10, 22):
        for x in range(8, 24):
            s.set_at((x, y), WINDOW)
    for y in range(10, 22):
        for x in range(8, 12):
            s.set_at((x, y), WIN_D)
    for y in range(42, 52):
        for x in range(8, 24):
            s.set_at((x, y), WINDOW)
    for y in range(42, 52):
        for x in range(8, 11):
            s.set_at((x, y), WIN_D)
    for x in range(8, 14):
        for y in range(5, 8):
            s.set_at((x, y), LIGHT_F)
    for x in range(18, 24):
        for y in range(5, 8):
            s.set_at((x, y), LIGHT_F)
    for x in range(8, 14):
        for y in range(57, 60):
            s.set_at((x, y), LIGHT_R)
    for x in range(18, 24):
        for y in range(57, 60):
            s.set_at((x, y), LIGHT_R)

    def draw_wheel(cx, cy):
        for dx in range(-4, 5):
            for dy in range(-5, 6):
                if abs(dx) + abs(dy) < 8:
                    s.set_at((cx + dx, cy + dy), WHEEL)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                s.set_at((cx + dx, cy + dy), RIM)

    draw_wheel(3, 14); draw_wheel(28, 14)
    draw_wheel(3, 50); draw_wheel(28, 50)
    return s


# ═══════════════════════════════════════════════════════════════════════════
#  COIN  (16 × 16 px, gold pixel art)
# ═══════════════════════════════════════════════════════════════════════════
def make_coin() -> pygame.Surface:
    W, H = 16, 16
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    s.fill((0, 0, 0, 0))

    GOLD   = (255, 200,  0)
    BRIGHT = (255, 240, 120)
    DARK   = (180, 120,  0)
    SHINE  = (255, 255, 200)

    # Circle mask
    for x in range(W):
        for y in range(H):
            dx, dy = x - 7.5, y - 7.5
            if dx*dx + dy*dy <= 7.5**2:
                s.set_at((x, y), GOLD)

    # Inner darker ring
    for x in range(W):
        for y in range(H):
            dx, dy = x - 7.5, y - 7.5
            r2 = dx*dx + dy*dy
            if 4.5**2 <= r2 <= 6**2:
                s.set_at((x, y), DARK)

    # Dollar / coin detail — simple "$" rendered as pixels
    # Vertical bar
    for y in range(4, 12):
        s.set_at((8, y), DARK)
    # Top arc
    for x in range(6, 11):
        s.set_at((x, 4), DARK)
        s.set_at((x, 8), DARK)
        s.set_at((x, 12), DARK)
    s.set_at((11, 5), DARK); s.set_at((11, 6), DARK)
    s.set_at((5, 10), DARK); s.set_at((5, 11), DARK)

    # Shine dot (top-left)
    s.set_at((5, 4), SHINE)
    s.set_at((6, 4), SHINE)
    s.set_at((5, 5), SHINE)

    return s


# ═══════════════════════════════════════════════════════════════════════════
#  ROAD BACKGROUND  (400 × 600 px tile)
# ═══════════════════════════════════════════════════════════════════════════
def make_road_bg() -> pygame.Surface:
    W, H = 400, 600
    s = pygame.Surface((W, H))

    ASPHALT    = ( 45,  45,  50)
    ASPHALT_L  = ( 55,  55,  60)   # lighter strip
    GRASS      = ( 30,  90,  30)
    GRASS_L    = ( 40, 110,  40)
    LINE       = (220, 220,  60)   # lane divider yellow
    CURB_W     = (230, 230, 230)
    CURB_R     = (200,  40,  40)

    # ── Grass strips (left and right)
    s.fill(GRASS)
    for x in range(0, W, 8):
        for y in range(0, H, 16):
            pygame.draw.line(s, GRASS_L, (x, y), (x+4, y+8), 1)

    # ── Road body
    pygame.draw.rect(s, ASPHALT, (60, 0, W - 120, H))
    # Subtle texture stripes
    for y in range(0, H, 6):
        pygame.draw.line(s, ASPHALT_L, (61, y), (W-61, y), 1)

    # ── Kerb (alternating red/white, 10px wide each side)
    block_h = 40
    for i, y in enumerate(range(0, H, block_h)):
        col = CURB_W if i % 2 == 0 else CURB_R
        pygame.draw.rect(s, col, (60, y, 12, block_h))
        pygame.draw.rect(s, col, (W - 72, y, 12, block_h))

    # ── Lane dividers (dashed yellow)
    road_left = 72
    road_right = W - 72
    road_w = road_right - road_left
    lane_w = road_w // 3
    for lane in [1, 2]:
        lx = road_left + lane * lane_w
        for y in range(0, H, 40):
            pygame.draw.rect(s, LINE, (lx - 2, y, 4, 24))

    return s


# ═══════════════════════════════════════════════════════════════════════════
#  EXPLOSION FRAMES  (4 frames, 48 × 48 px each)
# ═══════════════════════════════════════════════════════════════════════════
def make_explosion_frames() -> list[pygame.Surface]:
    W = H = 48
    frames = []
    cx, cy = W // 2, H // 2

    colors_per_frame = [
        [(255, 220, 50), (255, 150, 0)],                          # frame 0 – small yellow
        [(255, 200, 50), (255, 100, 0), (255, 50, 0)],            # frame 1 – medium orange
        [(255, 120, 0),  (200, 50, 0),  (255, 200, 50)],          # frame 2 – full blast
        [(150, 50, 0),   (100, 30, 0),  (80, 80, 80)],            # frame 3 – fading smoke
    ]
    radii = [10, 16, 22, 20]

    for fi, (cols, rad) in enumerate(zip(colors_per_frame, radii)):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))
        # Outer glow
        pygame.draw.circle(s, cols[-1], (cx, cy), rad)
        # Inner rings
        for i, col in enumerate(cols[:-1]):
            pygame.draw.circle(s, col, (cx, cy), rad - (i + 1) * 5)
        # Pixel sparks
        import random
        rng = random.Random(fi * 42)
        for _ in range(12):
            angle = rng.uniform(0, 6.28)
            dist  = rng.randint(rad // 2, rad + 4)
            sx = cx + int(dist * __import__('math').cos(angle))
            sy = cy + int(dist * __import__('math').sin(angle))
            if 0 <= sx < W and 0 <= sy < H:
                s.set_at((sx, sy), cols[0])
        frames.append(s)
    return frames


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Generating pixel-art assets …")

    save(make_player_car(), "player_car.png")
    save(make_enemy_car(),  "enemy_car.png")
    save(make_coin(),       "coin.png")
    save(make_road_bg(),    "road_bg.png")

    for i, frame in enumerate(make_explosion_frames()):
        save(frame, f"explosion_{i}.png")

    pygame.quit()
    print("Done! All assets saved to ./assets/")
