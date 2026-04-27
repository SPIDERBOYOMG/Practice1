"""
persistence.py
==============
JSON-backed save/load for leaderboard and user settings.
"""

import json
import os
import settings as S


# ── Paths ─────────────────────────────────────────────────────────────────────
_LB_PATH   = os.path.join(S.BASE_DIR, "leaderboard.json")
_CFG_PATH  = os.path.join(S.BASE_DIR, "settings.json")

# ── Default user settings ─────────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "sound":       True,
    "car_color":   "blue",
    "difficulty":  "normal",
}


# ── Leaderboard ───────────────────────────────────────────────────────────────

def load_leaderboard() -> list[dict]:
    """Return list of dicts: [{name, score, distance, coins, difficulty}]"""
    if not os.path.exists(_LB_PATH):
        return []
    try:
        with open(_LB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_leaderboard(entries: list[dict]) -> None:
    """Sort by score desc, keep top-10, write to disk."""
    sorted_entries = sorted(entries, key=lambda e: e.get("score", 0), reverse=True)
    top10 = sorted_entries[:10]
    with open(_LB_PATH, "w", encoding="utf-8") as f:
        json.dump(top10, f, indent=2)


def add_leaderboard_entry(name: str, score: int, distance: float,
                          coins: int, difficulty: str) -> list[dict]:
    """Append a new run result and persist. Returns updated top-10."""
    entries = load_leaderboard()
    entries.append({
        "name":       name,
        "score":      score,
        "distance":   round(distance, 1),
        "coins":      coins,
        "difficulty": difficulty,
    })
    save_leaderboard(entries)
    return load_leaderboard()


# ── User settings ─────────────────────────────────────────────────────────────

def load_settings() -> dict:
    """Load user preferences from settings.json, fall back to defaults."""
    if not os.path.exists(_CFG_PATH):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(_CFG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        cfg = DEFAULT_SETTINGS.copy()
        cfg.update({k: v for k, v in data.items() if k in DEFAULT_SETTINGS})
        return cfg
    except (json.JSONDecodeError, OSError):
        return DEFAULT_SETTINGS.copy()


def save_settings(cfg: dict) -> None:
    """Persist user preferences to settings.json."""
    with open(_CFG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
