# 🏎 PIXEL RACER — TSIS-3 Edition

Top-down pixel-art lane racer built with Pygame.  
Extends Practice 10–11 with full arcade features: power-ups, obstacles, difficulty scaling, persistent leaderboard, and complete UI flow.

---

## Running

```bash
pip install pygame
python main.py
```

Assets are auto-generated on first run if missing (`generate_assets.py`).

---

## Controls

| Key | Action |
|-----|--------|
| `← / A` | Move left |
| `→ / D` | Move right |
| `Q / ESC` | Quit to main menu |
| `R` | Retry (Game Over screen) |

---

## Features

### Screens & UI flow
```
Main Menu → Name Entry → Race → Game Over → (Leaderboard auto-saved)
                ↓
           Leaderboard
                ↓
            Settings
```

All screens built with pure Pygame — no external UI libraries.

### Power-ups

| Icon | Name    | Effect                          | Duration        |
|------|---------|---------------------------------|-----------------|
| ⚡   | Nitro   | Speed boost (+4 px/frame)       | 4 seconds       |
| 🛡   | Shield  | Absorbs one collision           | Until hit       |
| 🔧   | Repair  | Clears all road obstacles       | Instant         |

- Only one power-up active at a time.
- Power-ups blink and expire after 8 seconds if not collected.
- Active power-up + countdown shown in the HUD.

### Road obstacles

| Obstacle   | Effect              |
|------------|---------------------|
| Pothole    | Crash (lethal)      |
| Oil Spill  | Slows player 2.5 s  |
| Barrier    | Crash (lethal)      |

### Road events
- **NitroStrip** — glowing yellow strip across the road; driving over it gives a temporary speed boost and +50 score.

### Difficulty scaling

| Setting    | Easy  | Normal | Hard  |
|------------|-------|--------|-------|
| Enemy delay| 120 f | 80 f   | 45 f  |
| Obstacles  | low   | medium | high  |
| Speed ramp | slow  | medium | fast  |
| Power-ups  | often | normal | rare  |

Difficulty is chosen in Settings and saved to `settings.json`.

### Weighted coins

| Tier      | Weight | Value | Score |
|-----------|--------|-------|-------|
| 🟫 Bronze | 60     | ×1    | +10   |
| ⚪ Silver | 25     | ×3    | +30   |
| 🟡 Gold   | 12     | ×5    | +50   |
| 💎 Gem    |  3     | ×10   | +100  |

### Enemy boost system
Every 5 coins collected, all enemy cars gain +0.8 px/frame extra speed (capped at 14). A flashing ⚠ DANGER banner warns the player. The HUD bar `ENEMY ████░` tracks the tier.

### Leaderboard
- Top-10 entries persisted to `leaderboard.json`.
- Each entry stores: name, score, distance, coins, difficulty.
- Viewable from the main menu at any time.

---

## File structure

```
TSIS3/
├── main.py             # Game class + application shell
├── sprites.py          # PlayerCar, EnemyCar, Coin, Obstacle, PowerUp, NitroStrip, Explosion
├── hud.py              # Heads-up display renderer
├── ui.py               # All non-gameplay screens (Menu, Settings, Leaderboard, Game Over, Name Entry)
├── persistence.py      # JSON save/load for leaderboard and settings
├── settings.py         # All constants and configuration tables
├── generate_assets.py  # One-time pixel-art PNG asset generator
├── leaderboard.json    # Auto-created on first run
├── settings.json       # Auto-created on first run
└── assets/
    ├── player_car.png
    ├── enemy_car.png
    ├── road_bg.png
    ├── coin.png
    └── explosion_0-3.png
```
