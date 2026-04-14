"""
Moving Ball Game – Pixel Edition
=================================
Arrow keys  → move the red ball (20 px per press)
ESC / close → quit
"""

import sys
import pygame
from ball import Ball

# ── Constants ──────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 600, 600
FPS = 60
TITLE = "Moving Ball – Pixel Edition"

# Pixel-art palette
BG_COLOR      = (245, 245, 235)   # off-white parchment
GRID_COLOR    = (225, 220, 210)   # subtle grid lines
BORDER_COLOR  = (40,  35,  30)    # near-black border
ACCENT_COLOR  = (220, 30,  30)    # red (matches ball)

# HUD font will be loaded as a pixel-style font
HUD_FONT_SIZE = 18


# ── Helpers ────────────────────────────────────────────────────────────────────
def draw_pixel_grid(surface: pygame.Surface) -> None:
    """Draw a faint 20-px grid to reinforce the pixel-art aesthetic."""
    for x in range(0, SCREEN_W, 20):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, SCREEN_H))
    for y in range(0, SCREEN_H, 20):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (SCREEN_W, y))


def draw_border(surface: pygame.Surface) -> None:
    """Draw a chunky pixel border around the play field."""
    pygame.draw.rect(surface, BORDER_COLOR, (0, 0, SCREEN_W, SCREEN_H), 6)
    # Corner accents
    size = 12
    for cx, cy in [(0, 0), (SCREEN_W - size, 0),
                   (0, SCREEN_H - size), (SCREEN_W - size, SCREEN_H - size)]:
        pygame.draw.rect(surface, ACCENT_COLOR, (cx, cy, size, size))


def draw_hud(surface: pygame.Surface, font: pygame.font.Font,
             ball: Ball) -> None:
    """Show current ball coordinates in the top-left corner."""
    text = font.render(
        f"X:{ball.x:>4}  Y:{ball.y:>4}",
        False,           # no antialiasing → crisp pixel text
        BORDER_COLOR,
    )
    surface.blit(text, (12, 8))


def draw_instructions(surface: pygame.Surface, font: pygame.font.Font) -> None:
    """Show a small hint at the bottom."""
    hint = font.render("ARROW KEYS to move  |  ESC to quit", False, BORDER_COLOR)
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 26))


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE)

    # Prefer a monospace / pixel font; fall back to the system default
    try:
        font = pygame.font.SysFont("Courier New", HUD_FONT_SIZE, bold=True)
    except Exception:
        font = pygame.font.Font(None, HUD_FONT_SIZE)

    clock = pygame.time.Clock()
    ball = Ball(SCREEN_W, SCREEN_H)

    while True:
        # ── Events ────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                ball.handle_keydown(event.key)

        # ── Draw ──────────────────────────────────────────────────────
        screen.fill(BG_COLOR)
        draw_pixel_grid(screen)
        ball.draw(screen)
        draw_border(screen)
        draw_hud(screen, font, ball)
        draw_instructions(screen, font)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
