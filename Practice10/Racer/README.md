# 🏎 PIXEL RACER

A retro pixel-art top-down lane racer built with **Pygame** for Practice 10.

```
╔══════════════════════════════════════╗
║  SCORE 001337    │    COINS  x 007   ║
║  SPEED   9.4     │                   ║
║                                      ║
║   ░░░░░░│░░░░░░░░░│░░░░░░░░│░░░░░░   ║
║         │         │        │         ║
║       [CAR]       │                  ║
║         │      [COIN]      │         ║
║         │         │     [ENEMY]      ║
╚══════════════════════════════════════╝
```

## Features

| Feature | Detail |
|---------|--------|
| **Pixel art** | All sprites procedurally generated at 32×64 px, upscaled 2× |
| **3 lanes** | Player and enemies follow lane positions |
| **Coins** | Random spawns, animated pulse, score bonus (+50 each) |
| **Coin HUD** | Top-right counter `COINS x 007` in yellow retro font |
| **Speed ramp** | Scroll speed grows continuously; enemy delay shrinks |
| **Explosion** | 4-frame pixel animation on collision |
| **Restart** | Press R on Game Over screen |

## Project structure

```
Practice10/racer/
├── main.py             # Game loop & Game class
├── sprites.py          # PlayerCar, EnemyCar, Coin, Explosion sprites
├── hud.py              # HUD renderer (score, speed, coins, game-over)
├── settings.py         # All constants in one place
├── generate_assets.py  # One-time pixel-art PNG generator
├── assets/             # Generated PNG files land here
│   ├── player_car.png
│   ├── enemy_car.png
│   ├── coin.png
│   ├── road_bg.png
│   └── explosion_0..3.png
└── README.md
```

## How to run

```bash
pip install pygame

# Optional: pre-generate sprites (main.py does this automatically on first run)
python generate_assets.py

# Launch!
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| `←` / `A` | Move left |
| `→` / `D` | Move right |
| `R` | Restart (Game Over only) |
| `Q` / `ESC` | Quit |

## Implementation notes

### Tutorial base (CodersLegacy Parts 1–3)
The game follows the tutorial structure:
- **Part 1** – Window, player sprite, keyboard movement, road scrolling
- **Part 2** – Enemy cars, collision detection, sprite groups
- **Part 3** – Score display, speed increase, game-over screen

### Extra features

**Coins (extra task 1)**
```python
# In Game._try_spawn_coin():
if random.random() < S.COIN_SPAWN_CHANCE:   # 0.8% chance per frame
    coin = Coin(self._img_coin, self.scroll_speed)
```
Coins use the same lane grid as cars and scroll at 80% road speed
so the player has time to react.

**Coin HUD (extra task 2)**
```python
# In HUD.draw():
coin_surf = self._font_big.render(f"x{coins:03d}", True, S.COL_COIN_TEXT)
screen.blit(coin_surf, (panel_x + 32, m + 14))
```
Panel rendered with semi-transparent background (SRCALPHA) so it
never obscures critical gameplay area.

**Pixel / retro style (extra task 3)**
- All sprites are 32×64 px and upscaled 2× with nearest-neighbor
- Monospace bold font for all HUD text
- Alternating red/white kerb blocks
- Yellow dashed lane dividers
- Color-tinted enemy cars for variety without extra assets
