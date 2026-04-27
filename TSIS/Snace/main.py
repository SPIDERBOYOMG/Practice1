"""
main.py  —  PIXEL SNAKE  (TSIS 4)
==================================
Entry point and screen-state manager.

States
------
  MENU        — username input + button selection
  PLAYING     — active game session
  GAME_OVER   — game-over overlay (handled inside game.py)
  LEADERBOARD — top-10 table fetched from DB
  SETTINGS    — preferences panel

Settings are loaded from settings.json on startup and saved on change.

Controls (menu)
  ↑↓          navigate buttons
  ENTER       activate selected button
  type keys   edit username

Controls (game)
  WASD / arrows   move snake
  R               retry after game over
  M               main menu after game over
  Q / ESC         quit at any time
"""

import sys
import json
import os
import pygame

import config as C
import db
from renderer import Renderer
from game import Game


# ── Preferences helpers ───────────────────────────────────────────────────────

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

_SNAKE_COLOR_CYCLE = [
    [40, 180, 40],    # green
    [80, 160, 255],   # blue
    [255, 80, 80],    # red
    [255, 200, 0],    # gold
    [200, 100, 255],  # purple
]


def load_prefs() -> dict:
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"snake_color": [40, 180, 40], "grid": True, "sound": True}


def save_prefs(prefs: dict) -> None:
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(prefs, f, indent=2)
    except Exception as exc:
        print(f"[settings] Could not save: {exc}")


# ════════════════════════════════════════════════════════════════════════════
#  ScreenManager
# ════════════════════════════════════════════════════════════════════════════

STATE_MENU        = "MENU"
STATE_PLAYING     = "PLAYING"
STATE_LEADERBOARD = "LEADERBOARD"
STATE_SETTINGS    = "SETTINGS"


class ScreenManager:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(C.TITLE)
        self.screen   = pygame.display.set_mode((C.WIN_W, C.TOTAL_H), pygame.SCALED)
        self.clock    = pygame.time.Clock()

        self.prefs    = load_prefs()
        self.renderer = Renderer(self.screen, self.prefs)

        # DB bootstrap (graceful degradation if DB is unavailable)
        self.db_ok = db.ensure_schema()
        if not self.db_ok:
            print("[main] DB unavailable — leaderboard disabled, scores won't be saved.")

        # Menu state
        self._state       : str  = STATE_MENU
        self._username    : str  = "PLAYER"
        self._selected_btn: int  = 0          # 0=PLAY 1=LEADERBOARD 2=SETTINGS 3=QUIT
        self._cursor_timer: int  = 0
        self._cursor_vis  : bool = True

        # Leaderboard cache
        self._lb_rows: list[dict] = []

        # Settings editing state
        self._settings_sel  : int  = 0        # 0=grid 1=sound 2=color
        self._settings_tmp  : dict = {}       # in-memory edits

        # Personal best (fetched when username is set / game starts)
        self._personal_best : int = 0

        # Game session
        self.game = Game()

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        while True:
            dt = self.clock.tick(C.FPS_DISPLAY)
            dt = min(dt, 100)

            # Cursor blink
            self._cursor_timer += dt
            if self._cursor_timer >= 530:
                self._cursor_timer = 0
                self._cursor_vis   = not self._cursor_vis

            self._handle_global_events()

            if self._state == STATE_MENU:
                self._update_menu(dt)
            elif self._state == STATE_PLAYING:
                self._update_playing(dt)
            elif self._state == STATE_LEADERBOARD:
                pass   # static screen
            elif self._state == STATE_SETTINGS:
                pass   # static screen

            self._draw()
            pygame.display.flip()

    # ── Global events (quit) ──────────────────────────────────────────────────

    def _handle_global_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    if self._state == STATE_PLAYING and not self.game.game_over:
                        self._go_menu()   # ESC during game → menu
                    else:
                        self._quit()

            self._dispatch_event(event)

    def _dispatch_event(self, event: pygame.event.Event) -> None:
        if self._state == STATE_MENU:
            self._handle_menu_event(event)
        elif self._state == STATE_PLAYING:
            self._handle_playing_event(event)
        elif self._state == STATE_LEADERBOARD:
            self._handle_leaderboard_event(event)
        elif self._state == STATE_SETTINGS:
            self._handle_settings_event(event)

    # ── Menu ─────────────────────────────────────────────────────────────────

    def _handle_menu_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        key = event.key

        # Username editing (text input)
        if key == pygame.K_BACKSPACE:
            self._username = self._username[:-1]
        elif key == pygame.K_RETURN:
            self._activate_menu_btn(self._selected_btn)
        elif key == pygame.K_UP:
            self._selected_btn = (self._selected_btn - 1) % 4
        elif key == pygame.K_DOWN:
            self._selected_btn = (self._selected_btn + 1) % 4
        elif event.unicode and event.unicode.isprintable() and len(self._username) < 18:
            self._username += event.unicode.upper()

    def _activate_menu_btn(self, idx: int) -> None:
        if idx == 0:   # PLAY
            self._start_game()
        elif idx == 1: # LEADERBOARD
            self._go_leaderboard()
        elif idx == 2: # SETTINGS
            self._go_settings()
        elif idx == 3: # QUIT
            self._quit()

    def _update_menu(self, dt_ms: float) -> None:
        pass  # menu is fully event-driven

    def _start_game(self) -> None:
        name = self._username.strip() or "PLAYER"
        self._username = name
        # Fetch personal best
        self._personal_best = db.get_personal_best(name) if self.db_ok else 0
        self.game.reset(name, self._personal_best)
        self._state = STATE_PLAYING

    def _go_menu(self) -> None:
        self._state        = STATE_MENU
        self._selected_btn = 0

    def _go_leaderboard(self) -> None:
        self._lb_rows = db.get_top10() if self.db_ok else []
        self._state   = STATE_LEADERBOARD

    def _go_settings(self) -> None:
        import copy
        self._settings_tmp = copy.deepcopy(self.prefs)
        self._settings_sel = 0
        self._state        = STATE_SETTINGS

    # ── Playing ──────────────────────────────────────────────────────────────

    def _handle_playing_event(self, event: pygame.event.Event) -> None:
        action = self.game.handle_event(event)
        if action == "RETRY":
            self._start_game()
        elif action == "MENU":
            self._go_menu()

    def _update_playing(self, dt_ms: float) -> None:
        result = self.game.update(dt_ms)
        # Update personal best in ScreenManager too
        if self.game.score > self._personal_best:
            self._personal_best = self.game.score

    # ── Leaderboard ──────────────────────────────────────────────────────────

    def _handle_leaderboard_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_b, pygame.K_ESCAPE, pygame.K_RETURN):
                self._go_menu()

    # ── Settings ─────────────────────────────────────────────────────────────

    def _handle_settings_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        key = event.key
        n_items = 3  # grid, sound, color

        if key == pygame.K_UP:
            self._settings_sel = (self._settings_sel - 1) % n_items
        elif key == pygame.K_DOWN:
            self._settings_sel = (self._settings_sel + 1) % n_items
        elif key in (pygame.K_RETURN, pygame.K_SPACE,
                     pygame.K_LEFT, pygame.K_RIGHT):
            self._toggle_setting(self._settings_sel, key)
        elif key == pygame.K_s:
            self.prefs = self._settings_tmp
            self.renderer.prefs = self.prefs
            save_prefs(self.prefs)
            self._go_menu()
        elif key in (pygame.K_b, pygame.K_ESCAPE):
            self._go_menu()   # discard changes

    def _toggle_setting(self, idx: int, key) -> None:
        if idx == 0:   # grid
            self._settings_tmp["grid"] = not self._settings_tmp.get("grid", True)
        elif idx == 1: # sound
            self._settings_tmp["sound"] = not self._settings_tmp.get("sound", True)
        elif idx == 2: # snake color
            colors = _SNAKE_COLOR_CYCLE
            cur    = self._settings_tmp.get("snake_color", colors[0])
            try:
                i = colors.index(cur)
            except ValueError:
                i = 0
            delta = -1 if key == pygame.K_LEFT else 1
            self._settings_tmp["snake_color"] = colors[(i + delta) % len(colors)]

    # ── Draw ─────────────────────────────────────────────────────────────────

    def _draw(self) -> None:
        if self._state == STATE_MENU:
            self.renderer.draw_menu(self._username, self._cursor_vis,
                                    self._selected_btn)

        elif self._state == STATE_PLAYING:
            self.game.draw(self.renderer)

        elif self._state == STATE_LEADERBOARD:
            self.renderer.draw_leaderboard(self._lb_rows)

        elif self._state == STATE_SETTINGS:
            self.renderer.draw_settings(self._settings_tmp, self._settings_sel)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _quit() -> None:
        pygame.quit()
        sys.exit()


# ════════════════════════════════════════════════════════════════════════════
#  Entry point
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ScreenManager().run()
