import pygame


class Ball:
    """
    Pixel-style red ball that moves with arrow keys.
    Radius: 25px (50x50 bounding box), step: 20px
    """

    RADIUS = 25
    STEP = 20
    COLOR = (220, 30, 30)        # pixel-art red
    SHADOW_COLOR = (120, 10, 10) # dark pixel shadow
    HIGHLIGHT_COLOR = (255, 120, 120)  # bright pixel highlight

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        # Start at the center
        self.x = screen_width // 2
        self.y = screen_height // 2

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------
    def move(self, dx: int, dy: int) -> None:
        """
        Move the ball by (dx, dy) pixels.
        Silently ignores the move if it would push the ball off-screen.
        """
        new_x = self.x + dx
        new_y = self.y + dy

        # Boundary check – ignore inputs that would go out of bounds
        if new_x - self.RADIUS < 0 or new_x + self.RADIUS > self.screen_width:
            return
        if new_y - self.RADIUS < 0 or new_y + self.RADIUS > self.screen_height:
            return

        self.x = new_x
        self.y = new_y

    def handle_keydown(self, key) -> None:
        """Translate arrow-key events into movement."""
        if key == pygame.K_UP:
            self.move(0, -self.STEP)
        elif key == pygame.K_DOWN:
            self.move(0, self.STEP)
        elif key == pygame.K_LEFT:
            self.move(-self.STEP, 0)
        elif key == pygame.K_RIGHT:
            self.move(self.STEP, 0)

    # ------------------------------------------------------------------
    # Drawing (pixel / retro style)
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw a chunky pixel-art style ball:
          • dark shadow circle (bottom-right offset)
          • main red circle
          • small bright highlight dot (top-left)
        """
        # Shadow
        pygame.draw.circle(
            surface,
            self.SHADOW_COLOR,
            (self.x + 4, self.y + 4),
            self.RADIUS,
        )
        # Main body
        pygame.draw.circle(
            surface,
            self.COLOR,
            (self.x, self.y),
            self.RADIUS,
        )
        # Pixel highlight (top-left quadrant, ~40 % of radius)
        highlight_r = max(1, self.RADIUS // 3)
        pygame.draw.circle(
            surface,
            self.HIGHLIGHT_COLOR,
            (self.x - self.RADIUS // 3, self.y - self.RADIUS // 3),
            highlight_r,
        )
