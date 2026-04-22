# 🐍 PIXEL SNAKE

Retro pixel-art Snake game built with Pygame for Practice 10.

## Features

| Task | Implementation |
|------|---------------|
| **1. Wall collision** | `Snake.move()` checks if new head exits `PLAY_LEFT/TOP/RIGHT/BOTTOM` bounds; sets `alive = False` |
| **2. Smart food placement** | `Food._random_pos()` builds a set of all inner cells, subtracts snake body, picks from the remainder |
| **3. Level system** | `LevelSystem.eat()` counts foods; every `FOOD_PER_LEVEL` (4) advances the level |
| **4. Speed increase** | Each level adds `SPEED_INCREMENT (1.5)` moves/sec; capped at `SPEED_MAX (22)` |
| **5. Score + level counter** | HUD bar shows `SCORE 000000` (left) and `LEVEL 01` (right) every frame |
| **6. Comments** | All files, classes, and methods are documented |

## Project structure

```
Practice10/snake/
├── main.py        # Game loop, fixed-step timer, input buffering
├── snake.py       # Snake, Food, LevelSystem, Direction (pure logic)
├── renderer.py    # All Pygame drawing (walls, grid, HUD, overlays)
├── settings.py    # Every constant in one place
└── README.md
```

## Running

```bash
pip install pygame
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| `↑ W` | Move up |
| `↓ S` | Move down |
| `← A` | Move left |
| `→ D` | Move right |
| `R` | Restart (Game Over only) |
| `Q / ESC` | Quit |

## Architecture

### Fixed-step movement timer
The snake doesn't move every display frame — instead a millisecond accumulator triggers one step per `1000 / speed` ms. This decouples rendering FPS from game speed, so the game feels consistent on any hardware.

```python
self.move_accumulator += dt
if self.move_accumulator >= interval:
    self.move_accumulator -= interval
    self._step()
```

### Border collision (`snake.py`)
```python
if (nc < S.PLAY_LEFT or nc > S.PLAY_RIGHT or
        nr < S.PLAY_TOP  or nr > S.PLAY_BOTTOM):
    self.alive = False
```

### Food placement (`snake.py`)
```python
all_cells = {(c, r) for c in range(PLAY_LEFT, PLAY_RIGHT+1)
                     for r in range(PLAY_TOP,  PLAY_BOTTOM+1)}
free = all_cells - set(snake.body)
return random.choice(list(free))
```

### Level + speed progression
- Level starts at 1, speed at **6 moves/sec**
- Every **4 apples** → level up, speed **+1.5 moves/sec**
- Maximum speed: **22 moves/sec** (level ~12)
- Score per apple: `10 × current_level`
