import pyglet
import math
import random
from pyglet import shapes
from pyglet.gl import *

window = pyglet.window.Window(fullscreen=True)
window.set_caption("Blop Ecosystem")
window.set_mouse_visible(False)

screen_width = window.width
screen_height = window.height

current_fps = 0.0
frame_count = 0
last_fps_update = 0.0

COLOR_DEFINITIONS = {
    (255, 50, 150): {"id": 0},
    (100, 255, 80): {"id": 1},
    (80, 220, 255): {"id": 2},
    (255, 220, 50): {"id": 3},
}

RELATION_MATRIX = {
    0: {0: 0.3, 1: -0.8, 2: 0.5, 3: -0.4},
    1: {0: -0.7, 1: 0.2, 2: -0.6, 3: 0.6},
    2: {0: 0.6, 1: -0.5, 2: 0.4, 3: -0.7},
    3: {0: -0.3, 1: 0.7, 2: -0.8, 3: 0.1},
}

GRID_SIZE = 200
grid = {}


class Blop:
    __slots__ = ('x', 'y', 'vx', 'vy', 'color', 'color_id', 'relations')
    
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-30, 30)
        self.vy = random.uniform(-30, 30)
        self.color = color
        self.color_id = COLOR_DEFINITIONS[color]["id"]
        self.relations = RELATION_MATRIX[self.color_id]
        
    def update(self, dt, spatial_grid):
        fx = fy = 0.0
        
        gx = int(self.x // GRID_SIZE)
        gy = int(self.y // GRID_SIZE)
        
        # Check nearby cells for interactions
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                cell = spatial_grid.get((gx + dx, gy + dy))
                if not cell:
                    continue
                for other in cell:
                    if other is self:
                        continue
                    dx_r = other.x - self.x
                    dy_r = other.y - self.y
                    d2 = dx_r * dx_r + dy_r * dy_r
                    if d2 > 90000 or d2 < 1:  # Increased from 40000 to 90000 (300 range)
                        continue
                    
                    relation = (self.relations.get(other.color_id, 0) + 
                               RELATION_MATRIX[other.color_id].get(self.color_id, 0)) * 0.5
                    
                    if abs(relation) < 0.01:
                        continue
                    
                    d = math.sqrt(d2)
                    # Increased force multiplier for stronger interactions
                    force = abs(relation) * (1.0 - d / 300.0) * 150.0
                    dx_n = dx_r / d
                    dy_n = dy_r / d
                    
                    if relation > 0:
                        fx += dx_n * force
                        fy += dy_n * force
                    else:
                        fx -= dx_n * force
                        fy -= dy_n * force
        
        # Apply forces with higher acceleration
        self.vx = (self.vx + fx * dt * 0.015) * 0.95
        self.vy = (self.vy + fy * dt * 0.015) * 0.95
        
        # Reduced random walk for more directed motion
        self.vx += random.uniform(-3, 3) * dt
        self.vy += random.uniform(-3, 3) * dt
        
        # Velocity clamping with higher max speed
        speed_sq = self.vx * self.vx + self.vy * self.vy
        if speed_sq > 12100:  # 110 m/s max
            speed = math.sqrt(speed_sq)
            s = 110.0 / speed
            self.vx *= s
            self.vy *= s
        
        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Boundary
        if self.x < 15:
            self.x = 15
            self.vx = abs(self.vx)
        elif self.x > screen_width - 15:
            self.x = screen_width - 15
            self.vx = -abs(self.vx)
        
        if self.y < 15:
            self.y = 15
            self.vy = abs(self.vy)
        elif self.y > screen_height - 15:
            self.y = screen_height - 15
            self.vy = -abs(self.vy)


blops = []
for color in COLOR_DEFINITIONS.keys():
    for _ in range(150): # Increased from 100 to 150 blops per color
        x = random.uniform(50, screen_width - 50)
        y = random.uniform(50, screen_height - 50)
        blops.append(Blop(x, y, color))

# Pre-create batch and circles for efficient rendering
batch = pyglet.graphics.Batch()
blop_shapes = []
for blop in blops:
    circle = shapes.Circle(blop.x, blop.y, 1.5, color=blop.color, batch=batch)
    circle.opacity = 200
    blop_shapes.append(circle)

# Cache labels
fps_label = pyglet.text.Label("", font_name='Consolas', font_size=24, x=20, y=screen_height - 30,
                              color=(100, 255, 100, 255))

matrix_x = screen_width - 260
matrix_y = screen_height - 40
matrix_labels = [
    pyglet.text.Label("╔ RELATION ╗", font_name='Consolas', font_size=10,
                     x=matrix_x, y=matrix_y, color=(100, 200, 255, 255)),
    pyglet.text.Label("  │  P   L   C   O", font_name='Consolas', font_size=9,
                     x=matrix_x, y=matrix_y - 15, color=(150, 180, 220, 255)),
    pyglet.text.Label("──┼──────────────", font_name='Consolas', font_size=9,
                     x=matrix_x, y=matrix_y - 26, color=(100, 120, 180, 255)),
]

for r in range(4):
    row = " ".join(f"{RELATION_MATRIX[r][c]:+.1f}" for c in range(4))
    matrix_labels.append(
        pyglet.text.Label(f"{['P','L','C','O'][r]}  │ {row}", font_name='Consolas',
                         font_size=9, x=matrix_x, y=matrix_y - 37 - r*11,
                         color=(200, 200, 200, 255))
    )


@window.event
def on_draw():
    global current_fps
    
    glClearColor(0, 0, 0, 1)
    window.clear()
    
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    
    # Update circle positions and draw
    for i, blop in enumerate(blops):
        blop_shapes[i].x = blop.x
        blop_shapes[i].y = blop.y
    
    batch.draw()
    
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Update and draw FPS
    fps_label.text = f"FPS: {int(current_fps)}"
    fps_label.draw()
    
    # Draw matrix labels
    for label in matrix_labels:
        label.draw()


@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.ESCAPE:
        window.close()


def update(dt):
    global current_fps, frame_count, last_fps_update, grid
    
    frame_count += 1
    last_fps_update += dt
    if last_fps_update >= 1.0:
        current_fps = frame_count / last_fps_update
        frame_count = 0
        last_fps_update = 0.0
    
    grid.clear()
    for blop in blops:
        cell = (int(blop.x // GRID_SIZE), int(blop.y // GRID_SIZE))
        if cell not in grid:
            grid[cell] = []
        grid[cell].append(blop)
    
    for blop in blops:
        blop.update(dt, grid)


pyglet.clock.schedule_interval(update, 1/60.0)

if __name__ == '__main__':
    pyglet.app.run()
