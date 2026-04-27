"""
db.py
=====
PostgreSQL interface for the Snake game — TSIS 4.

Provides safe wrappers around psycopg2 so the rest of the game
never touches raw SQL.  Every public function returns a plain Python
value (dict / list / int / None) so callers don't need to know about
database cursors.

Schema (run once):
------------------
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
"""

import config as C

try:
    import psycopg2
    import psycopg2.extras
    _PSYCOPG2_AVAILABLE = True
except ImportError:
    _PSYCOPG2_AVAILABLE = False


# ── Connection helper ─────────────────────────────────────────────────────────

def _connect():
    """Open and return a new psycopg2 connection, or raise RuntimeError."""
    if not _PSYCOPG2_AVAILABLE:
        raise RuntimeError("psycopg2 is not installed — run: pip install psycopg2-binary")
    return psycopg2.connect(
        host=C.DB_HOST,
        port=C.DB_PORT,
        dbname=C.DB_NAME,
        user=C.DB_USER,
        password=C.DB_PASS,
        connect_timeout=3,
    )


# ── Schema bootstrap ──────────────────────────────────────────────────────────

def ensure_schema() -> bool:
    """
    Create the players and game_sessions tables if they don't exist.
    Returns True on success, False if the DB is unreachable or psycopg2
    is missing (so the game can degrade gracefully).
    """
    try:
        conn = _connect()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS players (
                        id       SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS game_sessions (
                        id            SERIAL PRIMARY KEY,
                        player_id     INTEGER REFERENCES players(id),
                        score         INTEGER   NOT NULL,
                        level_reached INTEGER   NOT NULL,
                        played_at     TIMESTAMP DEFAULT NOW()
                    );
                """)
        conn.close()
        return True
    except Exception as exc:
        print(f"[db] Schema setup failed: {exc}")
        return False


# ── Player helpers ────────────────────────────────────────────────────────────

def get_or_create_player(username: str) -> int | None:
    """
    Return the player's id, creating a new row if the username is new.
    Returns None on any DB error.
    """
    try:
        conn = _connect()
        with conn:
            with conn.cursor() as cur:
                # Upsert: insert if not exists, return existing id otherwise
                cur.execute("""
                    INSERT INTO players (username)
                    VALUES (%s)
                    ON CONFLICT (username) DO NOTHING;
                """, (username,))
                cur.execute("SELECT id FROM players WHERE username = %s;", (username,))
                row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as exc:
        print(f"[db] get_or_create_player failed: {exc}")
        return None


# ── Save game result ──────────────────────────────────────────────────────────

def save_session(username: str, score: int, level_reached: int) -> bool:
    """
    Persist a finished game session.
    Automatically creates the player record if it doesn't exist.
    Returns True on success, False on any error.
    """
    try:
        player_id = get_or_create_player(username)
        if player_id is None:
            return False
        conn = _connect()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO game_sessions (player_id, score, level_reached)
                    VALUES (%s, %s, %s);
                """, (player_id, score, level_reached))
        conn.close()
        return True
    except Exception as exc:
        print(f"[db] save_session failed: {exc}")
        return False


# ── Leaderboard ───────────────────────────────────────────────────────────────

def get_top10() -> list[dict]:
    """
    Return the Top-10 all-time high scores as a list of dicts:
        [{'rank': 1, 'username': 'Alice', 'score': 980,
          'level': 7, 'played_at': datetime}, ...]
    Returns an empty list on any error.
    """
    try:
        conn = _connect()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT
                    ROW_NUMBER() OVER (ORDER BY gs.score DESC) AS rank,
                    p.username,
                    gs.score,
                    gs.level_reached AS level,
                    gs.played_at
                FROM game_sessions gs
                JOIN players p ON p.id = gs.player_id
                ORDER BY gs.score DESC
                LIMIT 10;
            """)
            rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as exc:
        print(f"[db] get_top10 failed: {exc}")
        return []


# ── Personal best ─────────────────────────────────────────────────────────────

def get_personal_best(username: str) -> int:
    """
    Return the player's highest score ever, or 0 if they have no sessions
    or the DB is unavailable.
    """
    try:
        conn = _connect()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT MAX(gs.score)
                FROM game_sessions gs
                JOIN players p ON p.id = gs.player_id
                WHERE p.username = %s;
            """, (username,))
            row = cur.fetchone()
        conn.close()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as exc:
        print(f"[db] get_personal_best failed: {exc}")
        return 0
