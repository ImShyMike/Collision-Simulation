""" A 2D collision simulation using Pygame. """

import math
import random
from collections import defaultdict

import pygame
from pygame.locals import MOUSEMOTION, MOUSEWHEEL, RESIZABLE, VIDEORESIZE, KEYDOWN

pygame.init()

# Configuration
WORLD_SIZE = (6000, 4500)
WINDOW_SIZE = (800, 600)
CURRENT_POSITION = [-WORLD_SIZE[0] / 2, -WORLD_SIZE[1] / 2]
NUM_DOTS = 1000
GRID_SIZE = 25

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (120, 0, 0)

# Set up the screen
screen = pygame.display.set_mode(WINDOW_SIZE, RESIZABLE, vsync=1)
pygame.display.set_caption("2D Collision Simulation")

# Set up the font
font = pygame.font.Font(None, 36)

# Precompute neighbor offsets
neighbor_offsets = [
    (dx, dy)
    for dx in [-1, 0, 1]
    for dy in [-1, 0, 1]
    if dx != 0 or dy != 0  # Skip the current cell
]

# Default zoom level
current_zoom = 1

class Dot:
    """Dot class to represent a single dot on the screen."""
    def __init__(self, pos: list, vel: list, color: tuple, dot_size: int):
        self.pos = pos
        self.vel = vel
        self.color = color
        self.size = dot_size
        self.visible = False

    def check_visibility(self):
        """Calculate if the dot is visible on the screen and return the value."""
        dot_pos = self.pos
        x, y = dot_pos[0] + CURRENT_POSITION[0], dot_pos[1] + CURRENT_POSITION[1]
        is_visible = (
            -self.size <= x * current_zoom <= WINDOW_SIZE[0] + self.size
            and -self.size <= y * current_zoom <= WINDOW_SIZE[1] + self.size
        )
        self.visible = is_visible
        return is_visible

    def update(self, grid):
        """Update the dot's position based on its velocity."""
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

        # Check for wall collisions and bounce
        if self.pos[0] < self.size or self.pos[0] > WORLD_SIZE[0] - self.size:
            self.vel[0] *= -1
            # Adjust position to avoid sticking to the wall
            self.pos[0] = max(self.size, min(self.pos[0], WORLD_SIZE[0] - self.size))

        if self.pos[1] < self.size or self.pos[1] > WORLD_SIZE[1] - self.size:
            self.vel[1] *= -1
            # Adjust position to avoid sticking to the wall
            self.pos[1] = max(self.size, min(self.pos[1], WORLD_SIZE[1] - self.size))

        # Add to the spatial grid
        grid[get_grid_cell(self.pos)].append(self)

    def is_visible(self):
        """Get if the dot is visible on the screen."""
        return self.visible


# Initialize dots with random positions, velocities, colors, and sizes
DOTS = [
    Dot(
        [random.randint(1, WORLD_SIZE[0] - 1), random.randint(1, WORLD_SIZE[1] - 1)],
        [random.uniform(-5, 5), random.uniform(-5, 5)],
        (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)),
        random.randint(13, GRID_SIZE - 6),
    )
    for _ in range(NUM_DOTS)
]


def get_grid_cell(position):
    """Calculate the grid cell for a given position, adjusting based on zoom."""
    adjusted_grid_size = GRID_SIZE / current_zoom
    return int(position[0] // adjusted_grid_size), int(
        position[1] // adjusted_grid_size
    )


def detect_collision(dot1, dot2):
    """Detect if two dots are colliding using bounding box first."""
    # First, use bounding box check to avoid unnecessary calculations
    dist_x = abs(dot1.pos[0] - dot2.pos[0])
    dist_y = abs(dot1.pos[1] - dot2.pos[1])
    if dist_x > dot1.size + dot2.size or dist_y > dot1.size + dot2.size:
        return False

    # Then, check the exact distance for circle-to-circle collision
    dx = dot1.pos[0] - dot2.pos[0]
    dy = dot1.pos[1] - dot2.pos[1]
    return dx * dx + dy * dy < (dot1.size + dot2.size) ** 2


def resolve_collision(dot1, dot2):
    """Resolve collision using 2D elastic collision formula."""
    # Position vectors of the two dots
    x1, y1 = dot1.pos
    x2, y2 = dot2.pos

    # Velocity vectors of the two dots
    vx1, vy1 = dot1.vel
    vx2, vy2 = dot2.vel

    # Calculate the normal and tangent vectors of the collision
    dx = x2 - x1
    dy = y2 - y1
    # Calculate the speed of each dot
    dist = math.hypot(dx, dy)  # Distance between centers
    nx, ny = dx / dist, dy / dist  # Normal vector

    # Calculate relative velocity along the normal axis
    dot_product = (vx2 - vx1) * nx + (vy2 - vy1) * ny

    if dot_product > 0:
        return  # No need to resolve if dots are moving away from each other

    # Apply elastic collision equations
    m1, m2 = dot1.size, dot2.size  # Masses of the dots
    coeff = 2 * dot_product / (m1 + m2)

    # Update velocities along the normal axis
    vx1 += coeff * m2 * nx
    vy1 += coeff * m2 * ny
    vx2 -= coeff * m1 * nx
    vy2 -= coeff * m1 * ny

    # Assign updated velocities back to the dots
    dot1.vel = [vx1, vy1]
    dot2.vel = [vx2, vy2]


if __name__ == "__main__":
    running = True
    is_paused = False
    clock = pygame.time.Clock()
    last_ball_positions = []
    text_update_counter = 0
    gui_text = []

    # Main loop
    while running:
        text_update_counter += 1

        # Handle events
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == pygame.K_e:
                    is_paused = not is_paused
                elif event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == MOUSEWHEEL:
                # Nonlinear zoom
                zoom_factor = 0.05 if event.y > 0 else -0.05
                zoom_speed = (
                    0.5 + current_zoom / 3
                )  # Zoom speed increases with current zoom
                new_zoom = current_zoom + zoom_factor * zoom_speed
                new_zoom = max(0.1, min(new_zoom, 3))

                # Adjust the current position to zoom into the mouse position
                CURRENT_POSITION[0] -= mouse_x / current_zoom - mouse_x / new_zoom
                CURRENT_POSITION[1] -= mouse_y / current_zoom - mouse_y / new_zoom
                current_zoom = new_zoom
            elif event.type == MOUSEMOTION:
                # Use the right mouse button for dragging
                if event.buttons[2]:
                    CURRENT_POSITION[0] += event.rel[0] / current_zoom
                    CURRENT_POSITION[1] += event.rel[1] / current_zoom
            elif event.type == VIDEORESIZE:
                # Handle window resizing
                WINDOW_SIZE = event.size
                screen = pygame.display.set_mode(WINDOW_SIZE, RESIZABLE)

        # Calculate physics if not paused
        if not is_paused:
            # Update visible dots
            grid = defaultdict(list)
            list(map(lambda dot: dot.update(grid), DOTS))

            # Update dot positions
            for cell, dots in grid.items():
                # Check for collisions within the same cell
                for i, dot1 in enumerate(dots):
                    for j in range(i + 1, len(dots)):
                        if detect_collision(dot1, dots[j]):
                            resolve_collision(dot1, dots[j])

                # Check for collisions with neighboring cells
                for offset in neighbor_offsets:
                    neighbor_cell = (cell[0] + offset[0], cell[1] + offset[1])

                    if neighbor_cell in grid:
                        for dot1 in dots:
                            for dot2 in grid[neighbor_cell]:
                                if detect_collision(dot1, dot2):
                                    resolve_collision(dot1, dot2)

        # Calculate what dots are visible on the screen
        visible_dots = 0
        for cell in grid:
            visible_dots += sum(map(Dot.check_visibility, grid[cell]))

        # Draw the background
        screen.fill(BLACK)

        # Draw the visible dots
        for dot in filter(Dot.is_visible, DOTS):
            dot_x = dot.pos[0] + CURRENT_POSITION[0]
            dot_y = dot.pos[1] + CURRENT_POSITION[1]
            size = dot.size * current_zoom
            if size >= 1:
                pygame.draw.circle(
                    screen,
                    dot.color,
                    (int(dot_x * current_zoom), int(dot_y * current_zoom)),
                    max(1, size)
                )
            else:
                screen.set_at(
                    (int(dot_x * current_zoom), int(dot_y * current_zoom)),
                    dot.color
                )

        # Calculate the world border rectangle relative to the current view and draw it
        border_rect = pygame.Rect(
            CURRENT_POSITION[0] * current_zoom,
            CURRENT_POSITION[1] * current_zoom,
            WORLD_SIZE[0] * current_zoom,
            WORLD_SIZE[1] * current_zoom,
        )
        pygame.draw.rect(screen, RED, border_rect, width=1)

        # Update the GUI text every 3 frames to improve performance
        if text_update_counter >= 3:
            gui_text.clear()
            text_update_counter = 0

            # Make the mouse coordinates and scale text
            world_mouse_x = (mouse_x / current_zoom) - CURRENT_POSITION[0]
            world_mouse_y = (mouse_y / current_zoom) - CURRENT_POSITION[1]
            coordinates_text = font.render(
                f"({round(world_mouse_x, 2)}, {round(world_mouse_y, 2)}) - {round(current_zoom, 2)}",
                font,
                WHITE,
            )
            gui_text.append(coordinates_text)

            # Make the FPS counter text
            fps = round(clock.get_fps())
            fps_text = font.render(f"FPS: {fps}", font, WHITE)
            gui_text.append(fps_text)

            # Make the dot counter text
            entity_text = font.render(f"Dots: {visible_dots}", font, WHITE)
            gui_text.append(entity_text)

        # Draw the GUI
        for i, text in enumerate(gui_text):
            screen.blit(text, (0, i * 30))

        # Update the display
        pygame.display.flip()

        # Cap the frame rate
        clock.tick(60)

    pygame.quit()
