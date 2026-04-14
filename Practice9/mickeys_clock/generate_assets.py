"""
Generate pixel art assets for Mickey's Clock.
Run this once to create the required images.
"""
import pygame
import sys

def create_mickey_hand(filename, color=(255, 255, 255), is_right=True):
    """Create a pixel art Mickey Mouse glove hand."""
    # 16x32 pixel hand pointing up
    width, height = 16, 48
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    WHITE = (255, 255, 255, 255)
    BLACK = (0, 0, 0, 255)
    OUTLINE = (30, 30, 30, 255)

    # Pixel art hand — drawn as a gloved hand pointing upward
    # Format: list of (x, y) pixel positions for filled pixels
    hand_pixels = [
        # Finger tip (top)
        (7, 0), (8, 0),
        (6, 1), (7, 1), (8, 1), (9, 1),
        (6, 2), (7, 2), (8, 2), (9, 2),
        (5, 3), (6, 3), (7, 3), (8, 3), (9, 3), (10, 3),
        (5, 4), (6, 4), (7, 4), (8, 4), (9, 4), (10, 4),
        (4, 5), (5, 5), (6, 5), (7, 5), (8, 5), (9, 5), (10, 5), (11, 5),
        (4, 6), (5, 6), (6, 6), (7, 6), (8, 6), (9, 6), (10, 6), (11, 6),
        (3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (8, 7), (9, 7), (10, 7), (11, 7), (12, 7),
        (3, 8), (4, 8), (5, 8), (6, 8), (7, 8), (8, 8), (9, 8), (10, 8), (11, 8), (12, 8),
        # Palm
        (3, 9),  (4, 9),  (5, 9),  (6, 9),  (7, 9),  (8, 9),  (9, 9),  (10, 9), (11, 9), (12, 9),
        (3, 10), (4, 10), (5, 10), (6, 10), (7, 10), (8, 10), (9, 10), (10, 10),(11, 10),(12, 10),
        (3, 11), (4, 11), (5, 11), (6, 11), (7, 11), (8, 11), (9, 11), (10, 11),(11, 11),(12, 11),
        (3, 12), (4, 12), (5, 12), (6, 12), (7, 12), (8, 12), (9, 12), (10, 12),(11, 12),(12, 12),
        (3, 13), (4, 13), (5, 13), (6, 13), (7, 13), (8, 13), (9, 13), (10, 13),(11, 13),(12, 13),
        (3, 14), (4, 14), (5, 14), (6, 14), (7, 14), (8, 14), (9, 14), (10, 14),(11, 14),(12, 14),
        (3, 15), (4, 15), (5, 15), (6, 15), (7, 15), (8, 15), (9, 15), (10, 15),(11, 15),(12, 15),
        # Wrist
        (4, 16), (5, 16), (6, 16), (7, 16), (8, 16), (9, 16), (10, 16),(11, 16),
        (4, 17), (5, 17), (6, 17), (7, 17), (8, 17), (9, 17), (10, 17),(11, 17),
        (5, 18), (6, 18), (7, 18), (8, 18), (9, 18), (10, 18),
        (5, 19), (6, 19), (7, 19), (8, 19), (9, 19), (10, 19),
        (5, 20), (6, 20), (7, 20), (8, 20), (9, 20), (10, 20),
        (5, 21), (6, 21), (7, 21), (8, 21), (9, 21), (10, 21),
        (5, 22), (6, 22), (7, 22), (8, 22), (9, 22), (10, 22),
        (5, 23), (6, 23), (7, 23), (8, 23), (9, 23), (10, 23),
    ]

    for (x, y) in hand_pixels:
        surf.set_at((x, y), WHITE)

    # Draw outline (simple border detection)
    outline_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    outline_surf.fill((0, 0, 0, 0))

    pixel_set = set(hand_pixels)
    for (x, y) in hand_pixels:
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
            nx, ny = x+dx, y+dy
            if (nx, ny) not in pixel_set and 0 <= nx < width and 0 <= ny < height:
                if outline_surf.get_at((nx, ny))[3] == 0:
                    outline_surf.set_at((nx, ny), OUTLINE)

    surf.blit(outline_surf, (0, 0))

    pygame.image.save(surf, filename)
    print(f"Saved {filename}")

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1, 1))

    create_mickey_hand(
        "/home/claude/Practice7/mickeys_clock/images/mickey_hand_right.png",
        is_right=True
    )
    create_mickey_hand(
        "/home/claude/Practice7/mickeys_clock/images/mickey_hand_left.png",
        is_right=False
    )
    pygame.quit()
    print("Assets generated!")
