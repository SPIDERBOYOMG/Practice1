# TSIS 4 — Snake Game: Database Integration & Advanced Gameplay

Classic Snake built with **Pygame** and **psycopg2**, extended with a PostgreSQL
leaderboard, poison food, power-ups, dynamic obstacles, and four polished game screens.

---

## Features

| Category | Feature |
|---|---|
| **Database** | PostgreSQL leaderboard · auto-save after game over · personal best |
| **Food** | APPLE / CHERRY / GOLDEN (weighted, timed) · **POISON** (shortens snake) |
| **Power-ups** | Speed Boost · Slow Motion · Shield (one-hit protection) |
| **Obstacles** | Random wall blocks from Level 3, safe spawn radius around snake |
| **Screens** | Main Menu · Game (HUD) · Game Over · Leaderboard · Settings |
| **Settings** | Snake colour · grid overlay · sound — persisted in `settings.json` |

---

## Project structure

```
TSIS4/
├── main.py          ← entry point, screen-state machine
├── game.py          ← game coordinator (one session)
├── snake.py         ← game logic: snake, food, power-ups, obstacles, levels
├── renderer.py      ← all Pygame drawing (all screens)
├── db.py            ← psycopg2 DB layer (schema, save, leaderboard, best)
├── config.py        ← all constants (replaces settings.py from Practice 11)
├── settings.json    ← saved user preferences
└── assets/          ← (sounds / images if added)
```

---

## Quick start

### 1 — Install dependencies

```bash
pip install pygame psycopg2-binary
```

### 2 — Create the PostgreSQL database

```sql
CREATE DATABASE snake_game;

\c snake_game

CREATE TABLE players (
    id       SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE game_sessions (
    id            SERIAL PRIMARY KEY,
    player_id     INTEGER REFERENCES players(id),
    score         INTEGER   NOT NULL,
    level_reached INTEGER   NOT NULL,
    played_at     TIMESTAMP DEFAULT NOW()
);
```

> **Tip:** The game calls `db.ensure_schema()` on startup and creates the
> tables automatically if they don't exist (requires the database itself
> to exist first).

### 3 — Configure the connection (if needed)

Edit the `DB_*` constants at the bottom of **`config.py`**:

```python
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "snake_game"
DB_USER = "postgres"
DB_PASS = "postgres"
```

The game degrades gracefully if the DB is unavailable — scores won't be
saved and the leaderboard will be empty, but gameplay continues normally.

### 4 — Run

```bash
python main.py
```

---

## Controls

### Main menu
| Key | Action |
|---|---|
| Type | Edit username |
| ↑ / ↓ | Navigate buttons |
| Enter | Activate selected button |

### In game
| Key | Action |
|---|---|
| WASD / Arrows | Move snake |
| ESC | Back to main menu |

### Game over
| Key | Action |
|---|---|
| R | Retry immediately |
| M | Main menu |
| Q / ESC | Quit |

### Leaderboard / Settings
| Key | Action |
|---|---|
| B / ESC | Back to main menu |
| ↑ / ↓ | Navigate settings rows |
| ← / → or Space | Change value |
| S | Save & back |

---

## Gameplay details

### Poison food 💀
- Dark-red diamond shape on the grid.
- Eating it **removes 2 tail segments**.
- If the snake is shortened to length ≤ 1 → **immediate game over**.

### Power-ups ⚡
One power-up at a time appears on the field for **8 seconds**.
After collection the effect lasts **5 seconds**.

| Symbol | Name | Effect |
|---|---|---|
| `»` | Speed Boost | ×1.7 speed |
| `«` | Slow Motion | ×0.5 speed |
| `★` | Shield | Absorbs the next lethal collision |

### Obstacles 🧱
Starting at **Level 3**, random wall blocks appear inside the arena.
- 4 blocks at level 3, +2 blocks per additional level (max 20).
- No block within 3 cells of the snake's head at spawn time.
- Food and power-ups never spawn on obstacle cells.
- Hitting an obstacle is an immediate game over (unless the Shield is active).

---

## Database schema

```sql
players (id, username)
game_sessions (id, player_id, score, level_reached, played_at)
```

`db.py` exports:
- `ensure_schema()` — creates tables on first run
- `get_or_create_player(username)` — upsert player
- `save_session(username, score, level_reached)` — persist result
- `get_top10()` — fetch leaderboard
- `get_personal_best(username)` — fetch best score

---

## Settings (`settings.json`)

| Key | Type | Default | Description |
|---|---|---|---|
| `snake_color` | `[R, G, B]` | `[40, 180, 40]` | Snake body colour |
| `grid` | `bool` | `true` | Show grid overlay |
| `sound` | `bool` | `true` | Sound on/off (framework only) |

Saved automatically when you press **S** in the Settings screen.
