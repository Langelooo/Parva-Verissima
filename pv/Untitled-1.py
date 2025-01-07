import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
import sympy as sp
import time
import pygame

# Initialize pygame for font rendering
pygame.init()

# Initialize global variables
last_x, last_y = 0, 0
angle_x, angle_y = 0.0, 0.0

# Function to handle mouse dragging for viewpoint interaction
def mouse_drag_callback(window, xpos, ypos):
    global last_x, last_y, angle_x, angle_y
    if glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS:
        dx = xpos - last_x
        dy = ypos - last_y
        angle_x += dx * 0.01  # Adjust sensitivity here
        angle_y += dy * 0.01
    last_x, last_y = xpos, ypos

# Function to parse the input equation and return a sympy expression
def parse_equation(eq):
    x, t = sp.symbols('x t')
    eq = eq.replace('^', '**')  # Replace power notation with Python's syntax
    parsed_eq = sp.sympify(eq)  # Parse the equation using sympy
    return parsed_eq

# Particle class that uses the equation for motion
class Particle:
    def __init__(self, equation):
        self.equation = equation  # Equation to compute position based on time
        self.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.time = 0.0

    def update(self, dt):
        # Update the particle position based on the equation
        self.time += dt
        # Use the equation to get the new x-position, y = 0, z = 0 for simplicity
        x_value = self.equation.subs('t', self.time)  # Evaluate the equation at time t
        self.position = np.array([x_value, 0.0, 0.0], dtype=np.float32)

# Setup OpenGL rendering
def init_opengl():
    glEnable(GL_DEPTH_TEST)  # Enable depth testing
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Set background color to black
    glPointSize(5.0)  # Set point size for particles

# Set up the projection matrix (for 3D view)
def setup_projection():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, 1920.0 / 1080.0, 0.1, 100.0)  # Perspective projection
    glTranslatef(0.0, 0.0, -10)  # Move the scene back

# Function to render the particle
def draw_particles(vbo):
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glVertexPointer(3, GL_FLOAT, 0, None)  # Only position, stride = 0
    glEnableClientState(GL_VERTEX_ARRAY)
    glDrawArrays(GL_POINTS, 0, 1)  # Draw a single point (particle)
    glDisableClientState(GL_VERTEX_ARRAY)

# Function to create a VBO for the particle
def create_vbo(particle):
    vertex_data = particle.position
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_DYNAMIC_DRAW)
    return vbo

# Basic function to display text on screen using pygame
def display_text(window, text, x, y):
    # Create a pygame surface with text
    font = pygame.font.SysFont('Arial', 24)  # Using Arial as a default font
    text_surface = font.render(text, True, (255, 255, 255))  # White text
    text_data = pygame.image.tostring(text_surface, 'RGBA', True)

    # Create an OpenGL texture from the text surface
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_surface.get_width(), text_surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    # Position the text on the OpenGL window
    glEnable(GL_TEXTURE_2D)
    glPushMatrix()
    glLoadIdentity()
    glTranslatef(x, y, 0)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex2f(0, 0)
    glTexCoord2f(1, 0)
    glVertex2f(text_surface.get_width(), 0)
    glTexCoord2f(1, 1)
    glVertex2f(text_surface.get_width(), text_surface.get_height())
    glTexCoord2f(0, 1)
    glVertex2f(0, text_surface.get_height())
    glEnd()
    glPopMatrix()
    glDisable(GL_TEXTURE_2D)

# Main simulation loop
def simulate_particles(window, particle, vbo):
    global angle_x, angle_y
    time_step = 0.01  # Time step for each frame
    equation_input = "x(t) = t^3 + 2*t"  # Default equation
    last_time = time.time()
    fps_limit = 60  # Set the frame rate limit (FPS)

    while not glfw.window_should_close(window):
        current_time = time.time()
        elapsed_time = current_time - last_time

        if elapsed_time < 1.0 / fps_limit:
            continue  # Wait until we reach the next frame
        last_time = current_time

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clear the screen and depth buffer
        glLoadIdentity()

        # Apply viewpoint transformations
        glRotatef(angle_y, 1.0, 0.0, 0.0)  # Rotate around X axis
        glRotatef(angle_x, 0.0, 1.0, 0.0)  # Rotate around Y axis

        # Update particle position based on the equation
        particle.update(time_step)

        # Update VBO data
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, particle.position.nbytes, particle.position)

        # Draw the particle (a single point)
        draw_particles(vbo)

        # Display equation input text
        display_text(window, f"Equation: {equation_input}", -0.9, 0.9)

        # Swap buffers
        glfw.swap_buffers(window)

        # Poll for events (including mouse drag and keyboard input)
        glfw.poll_events()

# Initialize GLFW
if not glfw.init():
    raise Exception("GLFW could not be initialized")

# Create a fullscreen window
window = glfw.create_window(1920, 1080, "Particle Motion Simulation", None, None)
if not window:
    glfw.terminate()
    raise Exception("GLFW window could not be created")

# Set the window to full-screen
glfw.set_window_size(window, 1920, 1080)  # Full-screen resolution (1920x1080)
glfw.set_window_pos(window, 0, 0)

# Set the window context
glfw.make_context_current(window)

# Set up mouse dragging callback for interactive viewpoint control
glfw.set_cursor_pos_callback(window, mouse_drag_callback)

# Prompt user for equation input
print("Enter the equation for particle motion (e.g., x(t) = t^3 + 2*t):")
equation_input = input()  # Get user input
parsed_equation = parse_equation(equation_input)

# Initialize particle with the parsed equation
particle = Particle(parsed_equation)

# Create VBO to store particle data
vbo = create_vbo(particle)

# Set OpenGL configurations
init_opengl()
setup_projection()

# Start the simulation
simulate_particles(window, particle, vbo)

# Clean up and exit
glfw.terminate()
pygame.quit()
