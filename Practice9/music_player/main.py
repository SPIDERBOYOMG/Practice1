"""
main.py — Music Player UI & Keyboard Controller
================================================
Keyboard Controls
-----------------
  P          Play / Resume
  S          Stop
  SPACE      Pause / Resume toggle
  N          Next track
  B          Previous (Back) track
  ↑ / +      Volume up
  ↓ / -      Volume down
  Q / ESC    Quit
"""

import sys
import os
import pygame
from player import MusicPlayer


# ---------------------------------------------------------------------------
# Theme & layout constants
# ---------------------------------------------------------------------------

WINDOW_W, WINDOW_H = 640, 420
FPS = 60
TITLE = "🎵  PyPlayer"

# Colour palette — dark retro-terminal aesthetic
C_BG        = (10,  10,  18)
C_PANEL     = (18,  18,  32)
C_BORDER    = (55,  55,  90)
C_ACCENT    = (100, 210, 255)    # cyan highlight
C_ACCENT2   = (255, 100, 180)   # pink accent
C_WHITE     = (235, 235, 245)
C_GREY      = (130, 130, 150)
C_GREY_DIM  = (60,  60,  80)
C_GREEN     = (80,  230, 130)
C_YELLOW    = (255, 220, 80)
C_RED       = (255, 90,  90)

# State badge colours
STATE_COLORS = {
    "PLAYING": C_GREEN,
    "PAUSED":  C_YELLOW,
    "STOPPED": C_RED,
}

# State badge icons
STATE_ICONS = {
    "PLAYING": "▶  PLAYING",
    "PAUSED":  "⏸  PAUSED",
    "STOPPED": "⏹  STOPPED",
}


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def draw_rounded_rect(surf, color, rect, radius=10, width=0):
    pygame.draw.rect(surf, color, rect, width, border_radius=radius)


def draw_progress_bar(surf, x, y, w, h, progress: float, track_col, fill_col, radius=4):
    """Draw a progress bar with a gradient-style fill."""
    # Track
    draw_rounded_rect(surf, track_col, (x, y, w, h), radius)
    # Fill
    fill_w = max(0, int(w * progress))
    if fill_w > 0:
        draw_rounded_rect(surf, fill_col, (x, y, fill_w, h), radius)
    # Playhead knob
    knob_x = x + fill_w
    knob_r  = h + 2
    pygame.draw.circle(surf, C_WHITE, (knob_x, y + h // 2), knob_r)
    pygame.draw.circle(surf, fill_col, (knob_x, y + h // 2), knob_r - 2)


def draw_volume_bar(surf, x, y, w, h, volume: float):
    """Vertical-style compact volume bar."""
    draw_rounded_rect(surf, C_GREY_DIM, (x, y, w, h), 3)
    fill_h = int(h * volume)
    if fill_h > 0:
        draw_rounded_rect(surf, C_ACCENT2, (x, y + h - fill_h, w, fill_h), 3)


def draw_waveform_decor(surf, x, y, w, h, progress: float, state: str):
    """
    Decorative animated 'waveform' bars that react to playback state.
    Bars to the left of the playhead are lit; to the right are dim.
    """
    bar_count = 48
    bar_gap   = 2
    bar_w     = (w - bar_gap * (bar_count - 1)) // bar_count
    import math, time

    for i in range(bar_count):
        t = time.monotonic()
        # Height: sine wave with phase offset per bar
        phase = (i / bar_count) * math.pi * 4
        if state == "PLAYING":
            amp = 0.4 + 0.6 * abs(math.sin(t * 2.5 + phase))
        elif state == "PAUSED":
            amp = 0.3 + 0.2 * abs(math.sin(t * 0.5 + phase))
        else:
            amp = 0.05 + 0.08 * abs(math.sin(phase))

        bar_h = max(3, int(h * amp))
        bx = x + i * (bar_w + bar_gap)
        by = y + (h - bar_h) // 2

        played = (i / bar_count) <= progress
        col = C_ACCENT if played else C_GREY_DIM
        pygame.draw.rect(surf, col, (bx, by, bar_w, bar_h), border_radius=1)


# ---------------------------------------------------------------------------
# Key → action mapping
# ---------------------------------------------------------------------------

KEY_ACTIONS = {
    pygame.K_p:      "play",
    pygame.K_s:      "stop",
    pygame.K_SPACE:  "pause",
    pygame.K_n:      "next",
    pygame.K_b:      "prev",
    pygame.K_UP:     "vol_up",
    pygame.K_EQUALS: "vol_up",    # +
    pygame.K_PLUS:   "vol_up",
    pygame.K_DOWN:   "vol_down",
    pygame.K_MINUS:  "vol_down",
    pygame.K_q:      "quit",
    pygame.K_ESCAPE: "quit",
}


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

def run():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()

    # Locate music directory relative to this script
    music_dir = os.path.join(os.path.dirname(__file__), "music")

    try:
        player = MusicPlayer(music_dir)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    # Fonts — fall back gracefully if a nice font isn't found
    def load_font(size, bold=False):
        for name in ("Courier New", "Courier", "monospace", None):
            try:
                return pygame.font.SysFont(name, size, bold=bold)
            except Exception:
                continue
        return pygame.font.Font(None, size)

    font_huge  = load_font(32, bold=True)
    font_large = load_font(22, bold=True)
    font_med   = load_font(17)
    font_small = load_font(13)

    notification = {"text": "", "timer": 0}

    def notify(msg: str, duration: int = 120):
        notification["text"]  = msg
        notification["timer"] = duration

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    running = True
    while running:

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                action = KEY_ACTIONS.get(event.key)

                if action == "quit":
                    running = False

                elif action == "play":
                    player.play()
                    notify("▶  Play")

                elif action == "stop":
                    player.stop()
                    notify("⏹  Stopped")

                elif action == "pause":
                    player.pause()
                    notify("⏸  Paused" if player.state == "PAUSED" else "▶  Resumed")

                elif action == "next":
                    player.next_track()
                    notify(f"⏭  {player.current_track.title}")

                elif action == "prev":
                    player.prev_track()
                    notify(f"⏮  {player.current_track.title}")

                elif action == "vol_up":
                    player.volume_up()
                    notify(f"🔊  Volume {int(player.volume * 100)}%")

                elif action == "vol_down":
                    player.volume_down()
                    notify(f"🔉  Volume {int(player.volume * 100)}%")

        # Auto-advance when track ends
        player.tick()

        # --- Drawing ---
        screen.fill(C_BG)

        # ── Header bar ──────────────────────────────────────────────
        header_rect = (0, 0, WINDOW_W, 54)
        draw_rounded_rect(screen, C_PANEL, header_rect, radius=0)
        pygame.draw.line(screen, C_BORDER, (0, 54), (WINDOW_W, 54), 1)

        title_surf = font_huge.render("PyPlayer", True, C_ACCENT)
        screen.blit(title_surf, (24, 12))

        sub_surf = font_small.render("Keyboard Music Player", True, C_GREY)
        screen.blit(sub_surf, (26, 38))

        # Track counter top-right
        counter = f"{player.current_index + 1} / {player.track_count}"
        cs = font_med.render(counter, True, C_GREY)
        screen.blit(cs, (WINDOW_W - cs.get_width() - 24, 18))

        # ── Now Playing panel ────────────────────────────────────────
        panel_rect = (20, 70, WINDOW_W - 40, 110)
        draw_rounded_rect(screen, C_PANEL, panel_rect, radius=12)
        draw_rounded_rect(screen, C_BORDER, panel_rect, radius=12, width=1)

        # Album art placeholder (a coloured square with a note symbol)
        art_rect = (38, 82, 80, 86)
        art_colors = [
            (60, 30, 90), (20, 60, 80), (70, 20, 40),
            (20, 70, 50), (60, 50, 20),
        ]
        art_col = art_colors[player.current_index % len(art_colors)]
        draw_rounded_rect(screen, art_col, art_rect, radius=8)
        note_surf = font_huge.render("♪", True, C_ACCENT)
        screen.blit(note_surf, (art_rect[0] + 22, art_rect[1] + 22))

        # Track title
        track = player.current_track
        title_text = font_large.render(track.title, True, C_WHITE)
        screen.blit(title_text, (134, 86))

        # File name (smaller)
        fname_text = font_small.render(track.filename, True, C_GREY)
        screen.blit(fname_text, (135, 112))

        # State badge
        state_col  = STATE_COLORS[player.state]
        state_icon = STATE_ICONS[player.state]
        badge_surf = font_med.render(state_icon, True, state_col)
        bx = 134
        by = 132
        # dim badge bg
        bg_r = (bx - 6, by - 3, badge_surf.get_width() + 12, badge_surf.get_height() + 6)
        draw_rounded_rect(screen, (*state_col[:3], 30), bg_r, radius=6)  # type: ignore
        screen.blit(badge_surf, (bx, by))

        # Duration right side
        dur_surf = font_med.render(track.duration_str, True, C_GREY)
        screen.blit(dur_surf, (WINDOW_W - dur_surf.get_width() - 42, 86))

        # ── Waveform display ─────────────────────────────────────────
        wave_y = 196
        draw_waveform_decor(screen, 20, wave_y, WINDOW_W - 40, 48, player.progress, player.state)

        # ── Progress bar ─────────────────────────────────────────────
        bar_y = 256
        elapsed_surf = font_small.render(player.elapsed_str, True, C_GREY)
        total_surf   = font_small.render(track.duration_str, True, C_GREY)
        screen.blit(elapsed_surf, (20, bar_y + 10))
        screen.blit(total_surf,   (WINDOW_W - total_surf.get_width() - 20, bar_y + 10))

        draw_progress_bar(screen, 65, bar_y + 14, WINDOW_W - 130, 6,
                          player.progress, C_GREY_DIM, C_ACCENT)

        # ── Volume ───────────────────────────────────────────────────
        vol_label = font_small.render(f"VOL  {int(player.volume * 100):3d}%", True, C_ACCENT2)
        screen.blit(vol_label, (WINDOW_W - vol_label.get_width() - 20, 285))
        draw_volume_bar(screen, WINDOW_W - 20 - vol_label.get_width() - 14,
                        282, 8, 20, player.volume)

        # ── Playlist panel ───────────────────────────────────────────
        pl_y = 296
        pygame.draw.line(screen, C_BORDER, (20, pl_y - 6), (WINDOW_W - 20, pl_y - 6), 1)
        pl_label = font_small.render("PLAYLIST", True, C_ACCENT)
        screen.blit(pl_label, (20, pl_y))

        row_h = 22
        visible = 4
        for i, t in enumerate(player.playlist):
            if i >= visible:
                more = font_small.render(f"  + {player.track_count - visible} more …", True, C_GREY_DIM)
                screen.blit(more, (20, pl_y + 18 + i * row_h))
                break
            is_cur = (i == player.current_index)
            row_col = C_WHITE if is_cur else C_GREY
            prefix  = "▶ " if is_cur else f"{i+1}. "
            label   = font_small.render(f"{prefix}{t.title}  [{t.duration_str}]", True, row_col)
            if is_cur:
                hl = (18, pl_y + 16 + i * row_h - 1, label.get_width() + 8, row_h - 2)
                draw_rounded_rect(screen, C_GREY_DIM, hl, radius=4)
            screen.blit(label, (22, pl_y + 16 + i * row_h))

        # ── Keyboard hint bar ────────────────────────────────────────
        hints = "[P] Play  [S] Stop  [Space] Pause  [N] Next  [B] Back  [↑↓] Vol  [Q] Quit"
        hint_surf = font_small.render(hints, True, C_GREY_DIM)
        hint_y = WINDOW_H - hint_surf.get_height() - 6
        pygame.draw.line(screen, C_BORDER, (0, hint_y - 4), (WINDOW_W, hint_y - 4), 1)
        screen.blit(hint_surf, ((WINDOW_W - hint_surf.get_width()) // 2, hint_y))

        # ── Notification toast ───────────────────────────────────────
        if notification["timer"] > 0:
            alpha = min(255, notification["timer"] * 4)
            notif_surf = font_med.render(notification["text"], True, C_WHITE)
            nx = (WINDOW_W - notif_surf.get_width()) // 2
            ny = 62
            bg = (nx - 10, ny - 4, notif_surf.get_width() + 20, notif_surf.get_height() + 8)
            draw_rounded_rect(screen, C_PANEL, bg, radius=6)
            draw_rounded_rect(screen, C_ACCENT, bg, radius=6, width=1)
            screen.blit(notif_surf, (nx, ny))
            notification["timer"] -= 1

        pygame.display.flip()
        clock.tick(FPS)

    # Cleanup
    player.quit()
    pygame.quit()
    print("Bye! 🎵")


if __name__ == "__main__":
    run()
