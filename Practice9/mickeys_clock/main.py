"""
main.py — Mickey's Clock Application
=====================================
A pixel-art digital clock featuring Mickey Mouse's iconic glove hands.

  RIGHT hand (red)  → minutes
  LEFT  hand (cyan) → seconds

Controls:
  ESC / Q  → quit
  F        → toggle fullscreen
"""

import sys
import datetime
import pygame

from clock import MickeyClock


# ── Constants ──────────────────────────────────────────────────────────────
TITLE        = "Mickey's Clock"
WIN_WIDTH    = 480
WIN_HEIGHT   = 480
TARGET_FPS   = 60          # Smooth animation
UPDATE_MS    = 100         # Re-sample system time every 100 ms


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)

    # Try to set a pixel-art-friendly display mode
    flags = pygame.SCALED   # keeps integer scaling when resizing
    screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), flags)

    clock_widget = MickeyClock(screen)
    game_clock   = pygame.time.Clock()

    last_update  = pygame.time.get_ticks() - UPDATE_MS  # force first draw
    last_now     = datetime.datetime.now()

    fullscreen = False
    running    = True

    while running:
        # ── Events ────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    if fullscreen:
                        pygame.display.set_mode(
                            (WIN_WIDTH, WIN_HEIGHT),
                            pygame.FULLSCREEN | pygame.SCALED
                        )
                    else:
                        pygame.display.set_mode(
                            (WIN_WIDTH, WIN_HEIGHT),
                            pygame.SCALED
                        )

        # ── Time sampling ──────────────────────────────────────────────────
        ticks = pygame.time.get_ticks()
        if ticks - last_update >= UPDATE_MS:
            last_now    = datetime.datetime.now()
            last_update = ticks

        # ── Render ─────────────────────────────────────────────────────────
        clock_widget.render(last_now)
        pygame.display.flip()
        game_clock.tick(TARGET_FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
