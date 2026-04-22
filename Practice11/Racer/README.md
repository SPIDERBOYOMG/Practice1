# 🏎 PIXEL RACER  (extended)

Top-down pixel-art lane racer built with Pygame.

## New features

### 1. Weighted coins with different values

Four rarity tiers spawn on the road:

| Tier      | Weight | Value | Score bonus | Frequency |
|-----------|--------|-------|-------------|-----------|
| 🟫 Bronze | 60     | ×1    | +10         | ~60%      |
| ⚪ Silver | 25     | ×3    | +30         | ~25%      |
| 🟡 Gold   | 12     | ×5    | +50         | ~12%      |
| 💎 Gem    |  3     | ×10   | +100        |  ~3%      |

Each coin **displays its multiplier** (e.g. `×5`) and is drawn at a different size. Spawn uses a weighted-random draw in `pick_coin_type()`.

### 2. Enemy speed boost every N coins

Every **5 coins** collected, enemy cars gain **+0.8 px/frame** extra speed (cap: 12). A flashing ⚠ DANGER banner warns the player. The HUD bar `ENEMY ████░` shows progress toward the cap.

### 3. Full comments — every file, class, and method is documented.

## Structure

```
racer_extended/
├── main.py             # Game class + main loop
├── sprites.py          # PlayerCar, EnemyCar, Coin, Explosion, pick_coin_type()
├── hud.py              # HUD renderer, danger banner, game-over overlay
├── settings.py         # All constants: COIN_TYPES table, ENEMY_BOOST_* values
├── generate_assets.py  # One-time pixel-art PNG generator
└── assets/
```

## Running

```bash
pip install pygame
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| `← / A` | Move left |
| `→ / D` | Move right |
| `R` | Restart (Game Over only) |
| `Q / ESC` | Quit |

## Key implementation details

### Weighted coin selection (`sprites.py`)
```python
total = sum(ct["weight"] for ct in S.COIN_TYPES)
roll  = random.uniform(0, total)
for ct in S.COIN_TYPES:
    roll -= ct["weight"]
    if roll <= 0:
        return ct    # stops at the first type that consumed the roll
```

### Enemy boost on N coins (`main.py`)
```python
# Fires when coins_count crosses _boost_threshold
self._enemy_extra = min(self._enemy_extra + S.ENEMY_BOOST_AMOUNT,
                        S.ENEMY_SPEED_EXTRA_MAX)
self._danger_timer    = S.ENEMY_BOOST_FLASH_FRAMES
self._boost_threshold += S.ENEMY_BOOST_EVERY_N
```
All on-screen enemies update immediately — `EnemyCar.update()` receives `enemy_extra` every frame.
