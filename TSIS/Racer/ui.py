"""
ui.py
=====
All non-gameplay Pygame screens for PIXEL RACER – TSIS-3.

Screens
-------
NameEntryScreen   – ask for username before race
MainMenuScreen    – Play / Leaderboard / Settings / Quit
SettingsScreen    – sound toggle, car colour, difficulty
LeaderboardScreen – top-10 table
GameOverScreen    – final stats with Retry / Menu buttons
"""

import pygame
import settings as S
import persistence as P


# ── Colour helpers ─────────────────────────────────────────────────────────────
_C_BG      = (15, 15, 20)
_C_PANEL   = (25, 25, 35, 210)
_C_TITLE   = (255, 220, 40)
_C_TEXT    = (230, 230, 255)
_C_DIM     = (140, 140, 170)
_C_ACCENT  = (80, 160, 255)
_C_BTN     = (35, 35, 55)
_C_BTN_HOV = (55, 55, 90)
_C_BTN_ACT = (80, 130, 220)
_C_RED     = (220, 60, 60)
_C_GREEN   = (60, 200, 100)


def _font(size, bold=True):
    try:
        return pygame.font.SysFont("monospace", size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size + 4)


# ── Generic button helper ──────────────────────────────────────────────────────

class Button:
    def __init__(self, rect: pygame.Rect, label: str, font,
                 color=_C_BTN, hover_color=_C_BTN_HOV, text_color=_C_TEXT):
        self.rect        = rect
        self.label       = label
        self.font        = font
        self.color       = color
        self.hover_color = hover_color
        self.text_color  = text_color

    def draw(self, surf: pygame.Surface, mouse_pos):
        hov = self.rect.collidepoint(mouse_pos)
        bg  = self.hover_color if hov else self.color
        pygame.draw.rect(surf, bg, self.rect, border_radius=8)
        pygame.draw.rect(surf, _C_ACCENT, self.rect, 2, border_radius=8)
        lbl = self.font.render(self.label, True, self.text_color)
        surf.blit(lbl, lbl.get_rect(center=self.rect.center))

    def clicked(self, mouse_pos) -> bool:
        return self.rect.collidepoint(mouse_pos)


# ══════════════════════════════════════════════════════════════════════════════
#  Name Entry Screen
# ══════════════════════════════════════════════════════════════════════════════
class NameEntryScreen:
    """Ask the player to type a name before racing."""

    MAX_LEN = 14

    def __init__(self):
        self._f_title = _font(34)
        self._f_label = _font(18)
        self._f_input = _font(26)
        self._f_hint  = _font(13, bold=False)
        self._name    = ""
        self._cursor  = True
        self._cursor_t= 0

    def run(self, screen: pygame.Surface, clock) -> str | None:
        """
        Block until the user presses Enter (returns name) or Escape (returns None).
        """
        while True:
            dt = clock.tick(S.FPS) / 1000.0
            self._cursor_t += dt
            if self._cursor_t >= 0.5:
                self._cursor_t = 0
                self._cursor   = not self._cursor

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    if event.key == pygame.K_RETURN:
                        name = self._name.strip()
                        return name if name else "Player"
                    if event.key == pygame.K_BACKSPACE:
                        self._name = self._name[:-1]
                    elif len(self._name) < self.MAX_LEN and event.unicode.isprintable():
                        self._name += event.unicode

            self._draw(screen)
            pygame.display.flip()

    def _draw(self, surf: pygame.Surface):
        surf.fill(_C_BG)
        cx = S.WIN_W // 2

        title = self._f_title.render("PIXEL RACER", True, _C_TITLE)
        surf.blit(title, title.get_rect(centerx=cx, centery=160))

        label = self._f_label.render("Enter your name:", True, _C_TEXT)
        surf.blit(label, label.get_rect(centerx=cx, centery=260))

        # Input box
        box = pygame.Rect(cx - 130, 285, 260, 44)
        pygame.draw.rect(surf, (30, 30, 50), box, border_radius=8)
        pygame.draw.rect(surf, _C_ACCENT, box, 2, border_radius=8)

        display = self._name + ("|" if self._cursor else " ")
        inp = self._f_input.render(display, True, _C_TEXT)
        surf.blit(inp, inp.get_rect(center=box.center))

        hint = self._f_hint.render("Press Enter to confirm   Esc to cancel", True, _C_DIM)
        surf.blit(hint, hint.get_rect(centerx=cx, centery=360))


# ══════════════════════════════════════════════════════════════════════════════
#  Main Menu
# ══════════════════════════════════════════════════════════════════════════════
class MainMenuScreen:
    def __init__(self):
        self._f_title  = _font(38)
        self._f_sub    = _font(14, bold=False)
        self._f_btn    = _font(18)
        cx = S.WIN_W // 2
        bw, bh, gap = 200, 44, 12
        by = 280
        self._btns = {
            "play":   Button(pygame.Rect(cx - bw // 2, by,           bw, bh), "PLAY",        self._f_btn, _C_BTN_ACT, (100, 160, 255)),
            "lb":     Button(pygame.Rect(cx - bw // 2, by + bh+gap,  bw, bh), "LEADERBOARD", self._f_btn),
            "set":    Button(pygame.Rect(cx - bw // 2, by+(bh+gap)*2,bw, bh), "SETTINGS",    self._f_btn),
            "quit":   Button(pygame.Rect(cx - bw // 2, by+(bh+gap)*3,bw, bh), "QUIT",        self._f_btn, _C_RED, (240, 80, 80)),
        }
        self._scroll = 0

    def run(self, screen, clock) -> str:
        """Return 'play', 'leaderboard', 'settings', or 'quit'."""
        while True:
            clock.tick(S.FPS)
            mpos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        return "play"
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for name, btn in self._btns.items():
                        if btn.clicked(mpos):
                            return name

            self._draw(screen, mpos)
            pygame.display.flip()

    def _draw(self, surf, mpos):
        surf.fill(_C_BG)
        # Scrolling road stripes in background
        self._scroll = (self._scroll + 3) % 60
        for y in range(-self._scroll, S.WIN_H, 60):
            pygame.draw.rect(surf, (20, 20, 28), (S.ROAD_LEFT, y, S.ROAD_W, 30))
        cx = S.WIN_W // 2
        title = self._f_title.render("PIXEL RACER", True, _C_TITLE)
        surf.blit(title, title.get_rect(centerx=cx, centery=130))
        sub = self._f_sub.render("TSIS-3 EDITION", True, _C_DIM)
        surf.blit(sub, sub.get_rect(centerx=cx, centery=180))
        for btn in self._btns.values():
            btn.draw(surf, mpos)


# ══════════════════════════════════════════════════════════════════════════════
#  Settings Screen
# ══════════════════════════════════════════════════════════════════════════════
class SettingsScreen:
    def __init__(self):
        self._f_title  = _font(28)
        self._f_label  = _font(16)
        self._f_val    = _font(16, bold=False)
        self._f_btn    = _font(16)
        cx = S.WIN_W // 2
        self._back = Button(pygame.Rect(cx - 80, 530, 160, 40), "BACK", self._f_btn)

    def run(self, screen, clock, cfg: dict) -> dict:
        """Edit cfg in place; returns updated cfg dict."""
        while True:
            clock.tick(S.FPS)
            mpos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return cfg
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    P.save_settings(cfg)
                    return cfg
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._back.clicked(mpos):
                        P.save_settings(cfg)
                        return cfg
                    # Toggle / cycle options
                    x, y = mpos
                    if 150 <= x <= 300:
                        if 220 <= y <= 255:   # sound
                            cfg["sound"] = not cfg["sound"]
                        elif 290 <= y <= 325:  # car colour
                            colors = list(S.CAR_COLOR_TINTS.keys())
                            idx = colors.index(cfg.get("car_color", "blue"))
                            cfg["car_color"] = colors[(idx + 1) % len(colors)]
                        elif 360 <= y <= 395:  # difficulty
                            diffs = list(S.DIFFICULTY_PRESETS.keys())
                            idx = diffs.index(cfg.get("difficulty", "normal"))
                            cfg["difficulty"] = diffs[(idx + 1) % len(diffs)]

            self._draw(screen, mpos, cfg)
            pygame.display.flip()

    def _draw(self, surf, mpos, cfg):
        surf.fill(_C_BG)
        cx = S.WIN_W // 2
        title = self._f_title.render("SETTINGS", True, _C_TITLE)
        surf.blit(title, title.get_rect(centerx=cx, centery=100))

        rows = [
            (220, "Sound",      "ON" if cfg["sound"] else "OFF",
             _C_GREEN if cfg["sound"] else _C_RED),
            (290, "Car Colour", cfg.get("car_color", "blue").capitalize(), _C_ACCENT),
            (360, "Difficulty", cfg.get("difficulty", "normal").upper(), _C_TITLE),
        ]
        for y, label, value, vc in rows:
            lbl = self._f_label.render(label, True, _C_TEXT)
            surf.blit(lbl, (70, y))
            # Clickable value box
            box = pygame.Rect(cx - 10, y - 4, 160, 34)
            hov = box.collidepoint(mpos)
            pygame.draw.rect(surf, _C_BTN_HOV if hov else _C_BTN, box, border_radius=6)
            pygame.draw.rect(surf, _C_ACCENT, box, 1, border_radius=6)
            val = self._f_val.render(value, True, vc)
            surf.blit(val, val.get_rect(center=box.center))
            hint = self._f_val.render("  ← click to change", True, _C_DIM)
            surf.blit(hint, (box.right + 4, y + 6))

        note = pygame.font.SysFont("monospace", 12).render(
            "Settings saved automatically", True, _C_DIM)
        surf.blit(note, note.get_rect(centerx=cx, centery=480))
        self._back.draw(surf, mpos)


# ══════════════════════════════════════════════════════════════════════════════
#  Leaderboard Screen
# ══════════════════════════════════════════════════════════════════════════════
class LeaderboardScreen:
    def __init__(self):
        self._f_title  = _font(28)
        self._f_head   = _font(14)
        self._f_row    = _font(14, bold=False)
        self._f_btn    = _font(16)
        cx = S.WIN_W // 2
        self._back = Button(pygame.Rect(cx - 80, 540, 160, 40), "BACK", self._f_btn)

    def run(self, screen, clock):
        """Block until Back is clicked."""
        entries = P.load_leaderboard()
        while True:
            clock.tick(S.FPS)
            mpos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    return
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._back.clicked(mpos):
                        return
            self._draw(screen, mpos, entries)
            pygame.display.flip()

    def _draw(self, surf, mpos, entries):
        surf.fill(_C_BG)
        cx = S.WIN_W // 2
        title = self._f_title.render("LEADERBOARD", True, _C_TITLE)
        surf.blit(title, title.get_rect(centerx=cx, centery=55))

        # Header
        cols = [30, 60, 180, 270, 340]
        headers = ["#", "NAME", "SCORE", "DIST(m)", "DIFF"]
        for hx, ht in zip(cols, headers):
            s = self._f_head.render(ht, True, _C_ACCENT)
            surf.blit(s, (hx, 100))
        pygame.draw.line(surf, _C_DIM, (20, 118), (S.WIN_W - 20, 118), 1)

        if not entries:
            emp = self._f_row.render("No entries yet. Start racing!", True, _C_DIM)
            surf.blit(emp, emp.get_rect(centerx=cx, centery=280))
        else:
            for i, e in enumerate(entries[:10]):
                y   = 130 + i * 36
                row_col = [_C_TITLE, (200, 230, 255), _C_TEXT, _C_TEXT, _C_DIM]
                vals = [
                    f"{i + 1}",
                    str(e.get("name", "?"))[:10],
                    f"{e.get('score', 0):,}",
                    f"{e.get('distance', 0):.0f}",
                    str(e.get("difficulty", "-"))[:4].upper(),
                ]
                if i == 0:
                    pygame.draw.rect(surf, (40, 36, 10),
                                     pygame.Rect(18, y - 3, S.WIN_W - 36, 30),
                                     border_radius=4)
                for hx, val, vc in zip(cols, vals, row_col):
                    s = self._f_row.render(val, True, vc)
                    surf.blit(s, (hx, y))

        self._back.draw(surf, mpos)


# ══════════════════════════════════════════════════════════════════════════════
#  Game Over Screen
# ══════════════════════════════════════════════════════════════════════════════
class GameOverScreen:
    def __init__(self):
        self._f_huge  = _font(44)
        self._f_big   = _font(20)
        self._f_med   = _font(16)
        self._f_btn   = _font(18)
        cx = S.WIN_W // 2
        self._btn_retry = Button(pygame.Rect(cx - 180, 440, 150, 44),
                                 "RETRY", self._f_btn, _C_BTN_ACT, (100, 160, 255))
        self._btn_menu  = Button(pygame.Rect(cx + 30, 440, 150, 44),
                                 "MENU",  self._f_btn)

    def run(self, screen, clock,
            score: int, distance: float, coins: int,
            coin_value: int, name: str) -> str:
        """Return 'retry' or 'menu'."""
        while True:
            clock.tick(S.FPS)
            mpos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "menu"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        return "retry"
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        return "menu"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._btn_retry.clicked(mpos):
                        return "retry"
                    if self._btn_menu.clicked(mpos):
                        return "menu"
            self._draw(screen, mpos, score, distance, coins, coin_value, name)
            pygame.display.flip()

    def _draw(self, surf, mpos, score, distance, coins, coin_value, name):
        # Dark overlay
        overlay = pygame.Surface((S.WIN_W, S.WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surf.blit(overlay, (0, 0))

        cx = S.WIN_W // 2
        go = self._f_huge.render("GAME OVER", True, _C_RED)
        surf.blit(go, go.get_rect(centerx=cx, centery=160))

        driver = self._f_med.render(f"Driver: {name}", True, _C_DIM)
        surf.blit(driver, driver.get_rect(centerx=cx, centery=215))

        stats = [
            (f"SCORE    : {score:,}",      _C_TITLE),
            (f"DISTANCE : {distance:.0f} m", _C_TEXT),
            (f"COINS    : {coins}",         (255, 220, 0)),
            (f"VALUE    : {coin_value}",    (200, 255, 200)),
        ]
        for i, (text, col) in enumerate(stats):
            s = self._f_big.render(text, True, col)
            surf.blit(s, s.get_rect(centerx=cx, centery=270 + i * 36))

        self._btn_retry.draw(surf, mpos)
        self._btn_menu.draw(surf, mpos)

        hint = self._f_med.render("R = Retry    Esc = Menu", True, _C_DIM)
        surf.blit(hint, hint.get_rect(centerx=cx, centery=510))
