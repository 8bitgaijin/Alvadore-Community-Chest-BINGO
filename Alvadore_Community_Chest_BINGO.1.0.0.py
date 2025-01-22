# -*- coding: utf-8 -*-
"""
Created on Sat Nov 16 11:07:54 2024
@author: Shane William Martins
"""
###############
### Imports ###
###############
# Standard library imports
import logging
import math
import os
import platform
import random
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Third-party imports
try:
    import pygame
except ImportError as e:
    print(f"Required third-party module Pygame missing: {e}")  # Fallback to console output
    sys.exit(1)  # Fail fast if critical modules are unavailable


###############
### Logging ###
###############
# Constants
LOG_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5  # Number of rotated logs to keep

# Global logger variable
logger = None

def get_platform_log_dir():
    """
    Get the platform-specific default log directory.
    Returns a Path object.
    """
    if platform.system() == "Darwin":  # macOS
        return Path.home() / "Documents" / "Bingo"
    else:  # Windows/Linux fallback
        return Path.home() / "Documents" / "Bingo"


def test_directory_writable(directory):
    """
    Test if a directory is writable by creating and removing a temporary file.
    Returns True if writable, False otherwise.
    """
    try:
        test_path = directory / "test_write.tmp"
        with test_path.open("w") as test_file:
            test_file.write("test")
        test_path.unlink()  # Cleanup
        return True
    except Exception:
        return False


def get_log_file_path():
    """
    Determine the log file path based on platform and write permissions.
    Creates directories if needed but does not test write access directly here.
    """
    log_dir = get_platform_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

    # Test current directory for write permissions
    if test_directory_writable(Path(".")):
        return Path("bingo_log.txt").resolve()
    else:
        return log_dir / "bingo_log.txt"


def configure_logging():
    """
    Configure logging with both file and stream handlers.
    Fallback to console logging on failure.
    """
    global logger  # Declare logger as global to make it accessible elsewhere

    log_file = get_log_file_path()
    print(f"Log file path: {log_file}")  # Debugging help during startup

    try:
        # Create handlers
        stream_handler = logging.StreamHandler()
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=LOG_FILE_SIZE,
            backupCount=LOG_BACKUP_COUNT,
        )

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[stream_handler, file_handler],
        )

        logger = logging.getLogger("BingoApp")
        logger.info("Logging is configured!")
    except Exception as e:
        # Fallback to console-only logging
        print(f"Failed to initialize file logging: {e}")
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("BingoApp")
        logger.warning("File logging disabled; using console logging only.")


# Initialize logging
configure_logging()


######################
### Text To Speech ###
######################
# Optional dependency: pyttsx3 (TTS engine)
try:
    import pyttsx3
    logger.info("Text-to-speech engine (pyttsx3) imported successfully.")
except ImportError as e:
    logger.warning("Optional module 'pyttsx3' is missing. TTS features will be disabled.")


#########################
### Initialize Pygame ###
#########################
pygame.init()


################
### Settings ###
################
# Screen Dimensions
WIDTH, HEIGHT = 1920, 1080

# Colors
BACKGROUND_COLOR = (0, 0, 128)
FONT_COLOR = (255, 255, 255)
QUESTION_COLOR = (0, 0, 0)
HIGHLIGHT_COLOR = (173, 216, 230)

# Grid and Circle Settings
GRID_SIZE = 5.3  # Grid scaling factor for layout
CIRCLE_RADIUS = 55
REVIEW_CIRCLE_RADIUS = 200
PREVIOUS_CIRCLE_RADIUS = 70
SINGLE_DIGIT_X_OFFSET = 20
DROP_SHADOW_OFFSET = 2

# Messaging and Timing
ALL_BALLS_DRAWN_MSG = "All balls drawn! Reset to play again."
REVIEW_DURATION = 3
MESSAGE_TIMEOUT_DURATION = 5

# BINGO Setup
BINGO_RANGES = {
    'B': range(1, 16),
    'I': range(16, 31),
    'N': range(31, 46),
    'G': range(46, 61),
    'O': range(61, 76),
}
BINGO_PATTERNS = {
    "REGULAR": "Regular",
    "T": "T",
    "TOP_MIDDLE_BOTTOM": "Top-middle-bottom",
    "Y": "Y",
    "CROSS": "Cross",
    "ARROW": "Arrow",
    "BLACKOUT": "BLACKOUT",
}
CURRENT_BINGO_PATTERN = BINGO_PATTERNS["REGULAR"]

# File Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
pattern_filenames = {
    "T": "T.png",
    "BLACKOUT": "BLACKOUT.png",
    "ARROW": "Arrow.png",
    "CROSS": "Cross.png",
    "Y": "Y.png",
    "TOP_MIDDLE_BOTTOM": "tmb.png",
}

# Default confirm key is 'y' for 'yes'
KEY_CONFIRM = pygame.K_y

#BINGO Board constants
BALLS_PER_COLUMN = 15
CIRCLE_X_OFFSET = 40
CIRCLE_Y_OFFSET = 30
######################
### Text To Speech ###
######################

def setup_tts(preferred_voice=None):
    """
    Set up the TTS engine with platform-specific voice configurations.
    
    Args:
        preferred_voice (str): The preferred voice name or keyword. Defaults
                               to "male" on Windows and "Alex" on macOS.
    
    Returns:
        pyttsx3.Engine: Configured TTS engine.
    """
    try:
        tts_engine = pyttsx3.init()
        tts_engine.setProperty('rate', 150)  # Default speaking rate
    except Exception as e:
        logger.error(f"Failed to initialize TTS engine: {e}")
        return None  # Fail gracefully if TTS initialization fails

    # Determine the preferred voice based on platform
    if preferred_voice is None:
        os_type = platform.system()
        preferred_voice = "male" if os_type == "Windows" else "Alex"

    # Search for the preferred voice
    found_voice = False
    try:
        for voice in tts_engine.getProperty('voices'):
            if preferred_voice.lower() in voice.name.lower():
                tts_engine.setProperty('voice', voice.id)
                found_voice = True
                break
    except Exception as e:
        logger.error(f"Error retrieving or setting voices: {e}")
        return tts_engine  # Return the default engine even if voice selection fails

    if not found_voice:
        logger.warning(f"Preferred voice '{preferred_voice}' not found. Using default voice.")

    return tts_engine


# Initialize TTS engine
try:
    tts_engine = setup_tts()
    if tts_engine:
        logger.info("TTS engine initialized successfully.")
    else:
        logger.warning("TTS engine unavailable; text-to-speech features disabled.")
except Exception as e:
    logger.error(f"Unexpected error during TTS initialization: {e}")
    tts_engine = None


#############
### Fonts ###
#############
def load_font(size):
    """
    Load a font with the specified size.
    
    Args:
        size (int): The desired font size.
    
    Returns:
        pygame.font.Font: Loaded font object.
    """
    try:
        return pygame.font.Font(None, size)
    except Exception as e:
        logger.error(f"Failed to load font with size {size}: {e}")
        return None
    
    
# Fonts to load
NUMBER_FONT = load_font(100)
CONFIRMATION_FONT = load_font(100)
ANNOUNCE_FONT = load_font(700)
REVIEW_FONT = load_font(200)
PREVIOUS_FONT = load_font(80)
NUMBER_FONT_SIZE = 100


####################
### Screen Setup ###
####################
try:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("Alvadore Community Chest BINGO")
    logger.info("Screen setup completed successfully.")
except Exception as e:
    logger.error(f"Failed to set up screen: {e}")
    sys.exit(1)  # Exit if the screen setup fails, as it's critical



####################################
### Helper and Utility Functions ###
####################################
def initialize_balls():
    """
    Initializes and shuffles the balls list for BINGO.
    
    Returns:
        list: A shuffled list of BINGO balls.
    """
    try:
        balls = [
            f"{letter}{num}"
            for letter, nums in BINGO_RANGES.items()
            for num in nums
        ]
        random.shuffle(balls)
        logger.info("Initialized and shuffled balls.")
        return balls
    except Exception as e:
        logger.error(f"Failed to initialize balls: {e}")
        return []


def reset_board(state):
    """
    Resets the board to its initial state, saving the current balls.

    Args:
        state (dict): The current game state containing 'balls' and 'drawn_balls'.
    
    Returns:
        None
    """
    try:
        state["last_game"] = state["drawn_balls"].copy()
        state["balls"] = initialize_balls()
        state["drawn_balls"].clear()
        logger.info("Board has been reset.")
    except KeyError as e:
        logger.error(f"State key missing during board reset: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during board reset: {e}")


def restore_last_game(state):
    """
    Restores the last game state by reloading previously drawn balls.

    Args:
        state (dict): The current game state containing 'last_game' and 'drawn_balls'.
    
    Returns:
        None
    """
    try:
        if state.get("last_game"):  # Safely check if 'last_game' exists and is not empty
            state["drawn_balls"] = state["last_game"].copy()
            logger.info("Restored the previous game state.")
        else:
            logger.warning("No previous game state to restore.")
    except KeyError as e:
        logger.error(f"State key missing during game restore: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during game restore: {e}")


def speak_ball(ball_label, state=None, state_key=None):
    """Speak the ball label out loud, with optional flag-checking to ensure it's only spoken once per game state."""
    if state and state_key:
        if state.get(state_key, False):
            return  # Skip if already spoken for this state
        state[state_key] = True  # Set flag to indicate speech was made
    tts_engine.say(ball_label)
    tts_engine.runAndWait()


###################################
### Rendering/Display Functions ###
###################################
def clear_screen():
    """Clears the screen with the background color."""
    screen.fill(BACKGROUND_COLOR)


def draw_newest_ball(newest_ball):
    """Draws the newest ball in a large circle at the center of the screen."""
    main_x, main_y = WIDTH * 0.5, HEIGHT // 2
    pygame.draw.circle(screen, FONT_COLOR, (main_x, main_y), REVIEW_CIRCLE_RADIUS)
    main_text_surface = REVIEW_FONT.render(newest_ball, True, QUESTION_COLOR)
    main_text_rect = main_text_surface.get_rect(center=(main_x, main_y))
    screen.blit(main_text_surface, main_text_rect)


def draw_previous_balls(previous_balls):
    """Draws up to five previous balls in a vertical row on the left."""
    previous_balls_x = WIDTH // 7
    for i, ball in enumerate(reversed(previous_balls)):
        y_offset = HEIGHT // 5 + i * 150
        pygame.draw.circle(screen, FONT_COLOR, (previous_balls_x, y_offset), PREVIOUS_CIRCLE_RADIUS)
        text_surface = PREVIOUS_FONT.render(ball, True, QUESTION_COLOR)
        text_rect = text_surface.get_rect(center=(previous_balls_x, y_offset))
        screen.blit(text_surface, text_rect)


def draw_bingo_pattern(state):
    """Displays the Bingo pattern label and current pattern."""
    bingo_pattern_label = "Bingo pattern:"
    pattern_label_x = WIDTH * 0.7
    pattern_label_y = HEIGHT * 0.4
    pattern_value_x = pattern_label_x
    pattern_value_y = pattern_label_y + 50

    render_text_with_shadow(
        bingo_pattern_label, PREVIOUS_FONT, FONT_COLOR, QUESTION_COLOR,
        pattern_label_x, pattern_label_y
    )

    current_pattern = state["current_pattern"]
    pattern_image = state["pattern_images"].get(current_pattern)

    if pattern_image:
        image_rect = pattern_image.get_rect(center=(pattern_value_x + 200, pattern_value_y + 300))
        screen.blit(pattern_image, image_rect)
    else:
        render_text_with_shadow(
            BINGO_PATTERNS[current_pattern], PREVIOUS_FONT, FONT_COLOR, QUESTION_COLOR,
            pattern_value_x, pattern_value_y
        )


def render_text_with_shadow(text, font, color, shadow_color, x, y, shadow_offset=DROP_SHADOW_OFFSET):
    """
    Renders text with a drop shadow effect.

    Args:
        text (str): The text to render.
        font (pygame.font.Font): The font object to use for rendering.
        color (tuple): The color of the main text (R, G, B).
        shadow_color (tuple): The color of the shadow (R, G, B).
        x (int): The x-coordinate of the text.
        y (int): The y-coordinate of the text.
        shadow_offset (int): The offset for the shadow position.

    Returns:
        None
    """
    try:
        # Render and position the shadow
        shadow_surface = font.render(text, True, shadow_color)
        shadow_rect = shadow_surface.get_rect(topleft=(x + shadow_offset, y + shadow_offset))
        screen.blit(shadow_surface, shadow_rect)
        
        # Render and position the main text
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(topleft=(x, y))
        screen.blit(text_surface, text_rect)
        
        logger.info(f"Rendered text '{text}' with shadow at ({x}, {y}).")
    except Exception as e:
        logger.error(f"Failed to render text '{text}': {e}")


def calculate_animation_frame(
    start_pos, end_pos, start_radius, end_radius, start_font_size, end_font_size, t
):
    """
    Calculate the current position, radius, and font size based on the progress (t).
    
    Args:
        start_pos (tuple): Starting position (x, y).
        end_pos (tuple): Ending position (x, y).
        start_radius (int): Starting circle radius.
        end_radius (int): Ending circle radius.
        start_font_size (int): Starting font size.
        end_font_size (int): Ending font size.
        t (float): Progress ratio (0.0 to 1.0).

    Returns:
        tuple: Current position, radius, and font size.
    """
    current_x = start_pos[0] + t * (end_pos[0] - start_pos[0])
    current_y = start_pos[1] + t * (end_pos[1] - start_pos[1])
    current_radius = int(start_radius + t * (end_radius - start_radius))
    current_font_size = int(start_font_size + t * (end_font_size - start_font_size))
    return (current_x, current_y, current_radius, current_font_size)


def spawn_particles_for_frame(frame, particles, x, y, spawn_rate=3):
    """
    Spawns particles based on the current frame.

    Args:
        frame (int): Current animation frame.
        particles (list): List of existing particles.
        x (float): X-coordinate for particle spawning.
        y (float): Y-coordinate for particle spawning.
        spawn_rate (int): Number of particles to spawn per frame.

    Returns:
        None
    """
    if frame % 1 == 0:  # Adjust spawn frequency if needed
        for _ in range(spawn_rate):
            particles.append(spawn_particle(x, y, speed_range=(1, 5)))


def render_frame(particles, ball_label, font_size, x, y, radius):
    """
    Render the current frame with particles, ball, and text.

    Args:
        particles (list): List of particle objects.
        ball_label (str): Label to display on the ball.
        font_size (int): Font size for the label.
        x (float): X-coordinate of the ball.
        y (float): Y-coordinate of the ball.
        radius (int): Radius of the ball.

    Returns:
        None
    """
    screen.fill(BACKGROUND_COLOR)
    update_particles(particles, HIGHLIGHT_COLOR)  # Update and render particles
    pygame.draw.circle(screen, FONT_COLOR, (int(x), int(y)), radius)

    dynamic_font = pygame.font.Font(None, font_size)
    text_surface = dynamic_font.render(ball_label, True, QUESTION_COLOR)
    text_rect = text_surface.get_rect(center=(int(x), int(y)))
    screen.blit(text_surface, text_rect)
    pygame.display.flip()


def animate_ball_transition(
    start_pos, end_pos, start_radius, end_radius, start_font_size, end_font_size,
    ball_label, duration
):
    """
    Animates the ball and text transition between announcement and review states,
    with particle effects.

    Args:
        start_pos (tuple): Starting position (x, y).
        end_pos (tuple): Ending position (x, y).
        start_radius (int): Starting circle radius.
        end_radius (int): Ending circle radius.
        start_font_size (int): Starting font size.
        end_font_size (int): Ending font size.
        ball_label (str): The label to display on the ball.
        duration (float): Duration of the animation in seconds.

    Returns:
        None
    """
    clock = pygame.time.Clock()
    total_frames = int(duration * 60)  # Assuming 60 FPS
    current_frame = 0
    particles = []  # Persist particles within the animation scope

    while current_frame < total_frames:
        t = current_frame / total_frames
        current_x, current_y, current_radius, current_font_size = calculate_animation_frame(
            start_pos, end_pos, start_radius, end_radius, start_font_size, end_font_size, t
        )

        # Spawn particles for the current frame
        spawn_particles_for_frame(current_frame, particles, current_x, current_y)

        # Render the current frame
        render_frame(particles, ball_label, current_font_size, current_x, current_y, current_radius)

        clock.tick(60)
        current_frame += 1


def spawn_particle(x, y, distance_range=(25, 100), speed_range=(0.01, 0.2), 
                   lifetime_range=(30, 120), radius_range=(2, 5)):
    """
    Spawns a new particle with properties for animation or effects.

    Args:
        x (int): The x-coordinate of the particle's center.
        y (int): The y-coordinate of the particle's center.
        distance_range (tuple): Range for the offset distance from (x, y).
        speed_range (tuple): Range for the particle's velocity.
        lifetime_range (tuple): Range for the particle's lifetime in frames.
        radius_range (tuple): Range for the particle's size (radius).

    Returns:
        dict: A particle with randomized properties.
    """
    try:
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(*distance_range)
        speed = random.uniform(*speed_range)
        lifetime = random.uniform(*lifetime_range)
        radius = random.randint(*radius_range)

        return {
            "x": x + distance * math.cos(angle),
            "y": y + distance * math.sin(angle),
            "vx": speed * math.cos(angle),
            "vy": speed * math.sin(angle),
            "lifetime": lifetime,
            "radius": radius,
        }
    except Exception as e:
        logger.error(f"Failed to spawn particle at ({x}, {y}): {e}")
        return None


def update_particles(particles, highlight_color):
    """
    Updates and renders particles, removing expired ones.

    Parameters:
        particles (list): List of particle dictionaries.
        highlight_color (tuple): Color of the particles.
    """
    for particle in particles[:]:
        particle["x"] += particle["vx"]
        particle["y"] += particle["vy"]
        particle["lifetime"] -= 1
        if particle["lifetime"] <= 0:
            particles.remove(particle)
        else:
            pygame.draw.circle(
                screen,
                highlight_color,
                (int(particle["x"]), int(particle["y"])),
                particle["radius"],
            )


def update_and_render_particles(particles, highlight_color):
    """Updates and renders all particles."""
    update_particles(particles, highlight_color)


def render_bingo_letters(font_color):
    """Renders the Bingo column letters (B, I, N, G, O) with drop shadows."""
    left_margin = WIDTH // 25
    letter_y_offset = HEIGHT // 30
    row_height = HEIGHT // GRID_SIZE

    for row_number, letter in enumerate(BINGO_RANGES.keys()):
        number_y = row_number * row_height + row_height // 2
        letter_y = number_y + letter_y_offset

        letter_surface = NUMBER_FONT.render(letter, True, font_color)
        letter_rect = letter_surface.get_rect(center=(left_margin, letter_y))

        shadow_surface = NUMBER_FONT.render(letter, True, QUESTION_COLOR)
        shadow_rect = shadow_surface.get_rect(
            center=(left_margin + DROP_SHADOW_OFFSET, letter_y + DROP_SHADOW_OFFSET)
        )

        screen.blit(shadow_surface, shadow_rect)
        screen.blit(letter_surface, letter_rect)


def render_bingo_numbers(state, font_color, highlight_color, particles):
    """Renders the Bingo numbers and highlights drawn balls."""
    left_margin = WIDTH // 25
    right_margin = WIDTH // 50
    available_width = WIDTH - left_margin - right_margin
    col_width = available_width // 16
    row_height = HEIGHT // GRID_SIZE
    number_offset = left_margin + col_width

    newest_ball = state["drawn_balls"][-1] if state["drawn_balls"] else None

    for row_number, (letter, nums) in enumerate(BINGO_RANGES.items()):
        number_y = row_number * row_height + row_height // 2

        for jdx, num in enumerate(nums):
            x = number_offset + col_width * jdx
            ball_label = f"{letter}{num}"

            if ball_label in state["drawn_balls"]:
                if ball_label == newest_ball:
                    for _ in range(3):
                        particles.append(spawn_particle(x + 40, number_y + 30))
                pygame.draw.circle(
                    screen, highlight_color, (x + 40, number_y + 30), CIRCLE_RADIUS
                )

            text_x_offset = SINGLE_DIGIT_X_OFFSET if num < 10 else 0
            render_text_with_shadow(
                str(num), NUMBER_FONT, font_color, QUESTION_COLOR, x + text_x_offset, number_y
            )


def render_bingo_pattern(state, font_color):
    """Renders the current Bingo pattern at the bottom of the screen."""
    pattern_message = f"Pattern: {BINGO_PATTERNS[state['current_pattern']]}"
    message_surface = PREVIOUS_FONT.render(pattern_message, True, font_color)
    message_rect = message_surface.get_rect(center=(WIDTH // 2, HEIGHT - 50))

    shadow_surface = PREVIOUS_FONT.render(pattern_message, True, QUESTION_COLOR)
    shadow_rect = shadow_surface.get_rect(
        center=(WIDTH // 2 + DROP_SHADOW_OFFSET, HEIGHT - 50 + DROP_SHADOW_OFFSET)
    )

    screen.blit(shadow_surface, shadow_rect)
    screen.blit(message_surface, message_rect)


##############
### BOARDS ###
##############
### Review board ###
def display_ball_review(state):
    """
    Displays the newest ball large on the right and up to five previous balls stacked on the left.
    """
    clear_screen()

    # Display the newest ball
    newest_ball = state["drawn_balls"][-1]
    draw_newest_ball(newest_ball)

    # Display up to five previous balls
    previous_balls = state["drawn_balls"][-6:-1] if len(state["drawn_balls"]) > 1 else []
    draw_previous_balls(previous_balls)

    # Display the Bingo pattern
    draw_bingo_pattern(state)

    # Update the display to show all drawn elements
    pygame.display.flip()

    # Speak the newest ball
    speak_ball(newest_ball, state, "review_spoken")


### BINGO Board ###
def display_bingo_board(state, font_color, highlight_color):
    """
    Displays the board on the screen with current drawn ball highlights,
    adding particle effects for the newest ball.

    Args:
        state (dict): The current game state.
        font_color (tuple): The color for the text.
        highlight_color (tuple): The color for highlighted balls.

    Returns:
        None
    """
    # Step 1: Clear the screen
    clear_screen()

    # Step 2: Update particles
    if "particles" not in state:
        state["particles"] = []
    update_and_render_particles(state["particles"], highlight_color)

    # Step 3: Render Bingo elements
    render_bingo_letters(font_color)
    render_bingo_numbers(state, font_color, highlight_color, state["particles"])
    render_bingo_pattern(state, font_color)

    # Step 4: Render Confirmation Message (always redraw)
    confirmation_message = state.get("confirmation_message", "")
    display_confirmation(confirmation_message)


# Confirmation and input functions
def display_confirmation(message):
    """
    Displays a centered confirmation message with drop shadow.

    Args:
        message (str): The confirmation message to display.

    Returns:
        None
    """
    if not message:
        return  # No message to display

    shadow_surface = CONFIRMATION_FONT.render(message, True, QUESTION_COLOR)
    shadow_rect = shadow_surface.get_rect(center=(WIDTH // 2 + DROP_SHADOW_OFFSET, HEIGHT * 0.25 + DROP_SHADOW_OFFSET))
    screen.blit(shadow_surface, shadow_rect)
    
    text_surface = CONFIRMATION_FONT.render(message, True, FONT_COLOR)
    text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT * 0.25))
    screen.blit(text_surface, text_rect)


def handle_confirmation(state, key, action, flag_key):
    """
    Handles a confirmation response by executing the given action
    and clearing the associated state flag.

    Args:
        state (dict): The game state.
        key (int): The pressed key.
        action (callable): The function to call if the confirmation key is pressed.
        flag_key (str): The state flag key to clear.

    Returns:
        None
    """
    if key == KEY_CONFIRM:
        try:
            action(state)  # Perform the specified action
        except Exception as e:
            logging.error(f"Failed to execute action '{action.__name__}': {e}")
    state[flag_key] = False  # Clear the confirmation flag


def handle_confirmation_input(state, key):
    """Handle the reset confirmation response."""
    handle_confirmation(state, key, reset_board, "awaiting_confirmation")


def handle_restore_input(state, key):
    """Handle the restore confirmation response."""
    handle_confirmation(state, key, restore_last_game, "awaiting_restore_confirmation")


def handle_auto_mode_input(state, event):
    """
    Handle inputs specific to auto mode.

    Args:
        state (dict): The current game state.
        event (pygame.event.Event): The event being processed.

    Returns:
        None
    """
    if not isinstance(state, dict) or not hasattr(event, "key"):
        logging.error("Invalid input: state or event is malformed.")
        return

    try:
        if event.key == pygame.K_SPACE and not state["is_announcing"]:
            draw_ball(state)
    except Exception as e:
        logging.error(f"Error while handling SPACE key: {e}")
        
        
### Gameplay/Logic Functions ###
def draw_next_ball(state):
    """
    Draw the next ball from the state.

    Args:
        state (dict): The current game state.

    Returns:
        str or None: The drawn ball, or None if no balls are left.
    """
    if not state.get("balls"):
        logging.warning("Attempted to draw a ball from an empty list.")
        return None

    ball = state["balls"].pop(0)
    state["drawn_balls"].append(ball)
    state["current_ball"] = ball
    logging.info(f"Drew ball: {ball}")
    return ball


def enter_review_mode(state, ball):
    """
    Set the state to review mode for the drawn ball.

    Args:
        state (dict): The current game state.
        ball (str): The ball to set as the current one in review mode.

    Returns:
        None
    """
    if not isinstance(state, dict):
        logging.error("Invalid state: Expected a dictionary.")
        return

    if not isinstance(ball, str):
        logging.error("Invalid ball: Expected a string.")
        return

    try:
        state["is_reviewing"] = True
        state["review_start_time"] = time.time()
        state["review_spoken"] = False
        state["current_ball"] = ball
    except Exception as e:
        logging.error(f"Error entering review mode: {e}")


def handle_no_balls_left(state):
    """
    Handle the case when no balls are left to draw.

    Args:
        state (dict): The current game state.

    Returns:
        None
    """
    try:
        if not isinstance(state, dict) or "message_timeout" not in state:
            logging.error("Invalid state: Missing required keys.")
            return

        if state["message_timeout"] <= time.time():
            logging.warning("All balls have been drawn.")
            display_confirmation(ALL_BALLS_DRAWN_MSG)
            state["message_timeout"] = time.time() + MESSAGE_TIMEOUT_DURATION
    except Exception as e:
        logging.error(f"Error handling no balls left: {e}")


def draw_ball(state):
    """
    Draws the next ball or handles cases where all balls are drawn.

    Args:
        state (dict): The current game state.

    Returns:
        None
    """
    try:
        if not isinstance(state, dict):
            logging.error("Invalid state: Expected a dictionary.")
            return

        ball = draw_next_ball(state)
        if ball:
            enter_review_mode(state, ball)
        else:
            handle_no_balls_left(state)
    except Exception as e:
        logging.error(f"Unexpected error in draw_ball: {e}")


def interpret_ball_number(ball_number):
    """
    Converts a numeric ball entry to the corresponding Bingo label.

    Args:
        ball_number (int or str): The numeric ball entry to interpret.

    Returns:
        str: The Bingo label (e.g., "B10") or None if invalid.
    """
    try:
        ball_number = int(ball_number)
        for letter, nums in BINGO_RANGES.items():
            if ball_number in nums:
                return f"{letter}{ball_number}"
        logging.warning(f"Invalid ball number entered: {ball_number}")
        return None  # Invalid Bingo number
    except ValueError:
        logging.warning(f"Non-integer input received: {ball_number}")
        return None


def process_typed_number(state):
    """Process the currently typed number when Enter is pressed."""
    ball_number = state.get("typed_number", "")
    logging.info(f"Enter key pressed. Typed number: {ball_number}")

    if ball_number:
        try:
            ball_number = int(ball_number)
            ball_label = interpret_ball_number(ball_number)
            logging.info(f"Interpreted ball label: {ball_label}")

            if ball_label in state["drawn_balls"]:
                logging.warning(f"Ball {ball_label} is already drawn. Ignoring input.")
            elif ball_label in state["balls"]:
                # Valid ball, process it
                state["drawn_balls"].append(ball_label)
                state["balls"].remove(ball_label)
                state["current_ball"] = ball_label
                state["announcement_time"] = time.time()
                state["is_announcing"] = True
                logging.info(f"Successfully drew ball: {ball_label}")
            else:
                logging.warning(f"Invalid ball number entered: {ball_number}")
        except ValueError:
            logging.error("Non-numeric entry detected. Resetting input.")

    state["typed_number"] = ""  # Clear input after processing


def process_backspace(state):
    """Handle backspace input to modify typed number."""
    state["typed_number"] = state.get("typed_number", "")[:-1]
    logging.info(f"Backspace pressed. Current typed number: {state['typed_number']}")


def handle_undo_request(state):
    """Prompt for undo confirmation if there are drawn balls."""
    if state["drawn_balls"]:
        state["awaiting_undo_confirmation"] = True
        logging.info("Undo confirmation requested.")
    else:
        logging.warning("No balls to undo.")


def handle_manual_mode_input(state, event):
    """Handles input in manual mode, delegating to smaller functions."""
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_RETURN:
            process_typed_number(state)
        elif event.key == pygame.K_BACKSPACE:
            process_backspace(state)
        elif event.key == pygame.K_u:
            handle_undo_request(state)
        elif event.unicode.isnumeric():
            state["typed_number"] = state.get("typed_number", "") + event.unicode
            logging.info(f"Number key pressed. Current typed number: {state['typed_number']}")


def process_global_inputs(state, event):
    """Process inputs that apply globally, like quitting or switching modes."""
    if event.key == pygame.K_ESCAPE:
        state["running"] = False
        logging.info("Quit event received, exiting game.")
    elif event.key == pygame.K_m:
        state["is_manual_mode"] = True
        logging.info("Switched to manual mode.")
    elif event.key == pygame.K_a:
        state["is_manual_mode"] = False
        logging.info("Switched to auto mode.")
    elif event.key == pygame.K_r:
        state["awaiting_confirmation"] = True
        logging.info("Reset confirmation requested.")
    elif event.key == pygame.K_o:
        state["awaiting_restore_confirmation"] = True
        logging.info("Restore confirmation requested.")


def process_confirmation_inputs(state, event):
    """Process inputs related to confirmation prompts."""
    if state["awaiting_undo_confirmation"]:
        if event.key == pygame.K_y:
            last_ball = state["drawn_balls"].pop()
            state["balls"].insert(0, last_ball)
            logging.info(f"Undo confirmed: {last_ball}")
        elif event.key == pygame.K_n:
            logging.info("Undo canceled.")
        state["awaiting_undo_confirmation"] = False
        return True  # Indicate confirmation was handled

    elif state["awaiting_confirmation"]:
        handle_confirmation_input(state, event.key)
        return True  # Indicate confirmation was handled

    elif state["awaiting_restore_confirmation"]:
        handle_restore_input(state, event.key)
        return True  # Indicate confirmation was handled

    return False  # No confirmation state was active


def process_pattern_change(state, event):
    """Process inputs related to pattern changes."""
    if event.key == pygame.K_n:
        pattern_keys = list(BINGO_PATTERNS.keys())
        current_index = pattern_keys.index(state["current_pattern"])
        next_index = (current_index + 1) % len(pattern_keys)
        state["current_pattern"] = pattern_keys[next_index]
        state["pattern_change_time"] = time.time() + 2
        logging.info(f"Switched to pattern: {BINGO_PATTERNS[state['current_pattern']]}")


def handle_input(state):
    """Handles user input differently in manual and auto modes."""
    if state["is_announcing"] or state["is_reviewing"]:
        return

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state["running"] = False
            logging.info("Quit event received, exiting game.")

        elif event.type == pygame.KEYDOWN:
            # Handle confirmation inputs first
            if process_confirmation_inputs(state, event):
                return  # Stop further processing if confirmation handled

            # Process global inputs
            process_global_inputs(state, event)

            # Process pattern changes
            process_pattern_change(state, event)

            # Delegate to mode-specific input handlers
            if state["is_manual_mode"]:
                handle_manual_mode_input(state, event)
            else:
                handle_auto_mode_input(state, event)


def get_confirmation_message(state):
    """
    Returns the appropriate confirmation message based on the current game state.

    Args:
        state (dict): The current game state.

    Returns:
        str: The confirmation message to display, or None if no message.
    """
    if state["awaiting_confirmation"]:
        return "Reset the board? (Y/N)"
    elif state["awaiting_restore_confirmation"]:
        return "Restore the last board? (Y/N)"
    elif state["awaiting_undo_confirmation"]:
        return "Undo last ball? (Y/N)"
    elif state["message_timeout"] > time.time():
        return ALL_BALLS_DRAWN_MSG
    return None


def get_board_position(ball_label):
    """
    Calculates the final (x, y) position for a ball on the board.

    Args:
        ball_label (str): The label of the ball (e.g., "B10").

    Returns:
        tuple: The (x, y) position on the board.

    Raises:
        ValueError: If the ball_label is invalid.
    """
    if not ball_label or len(ball_label) < 2 or ball_label[0] not in "BINGO" or not ball_label[1:].isdigit():
        raise ValueError(f"Invalid ball label: {ball_label}")

    left_margin = WIDTH // 25
    right_margin = WIDTH // 50
    available_width = WIDTH - left_margin - right_margin
    col_width = available_width // 16
    row_height = HEIGHT // GRID_SIZE
    number_offset = left_margin + col_width

    column_index = (int(ball_label[1:]) - 1) % BALLS_PER_COLUMN
    row_index = "BINGO".index(ball_label[0])

    board_x = number_offset + col_width * column_index + CIRCLE_X_OFFSET
    board_y = row_index * row_height + row_height // 2 + CIRCLE_Y_OFFSET

    return board_x, board_y


### Render Function ###
def render(state, background_color, font_color, highlight_color):
    """
    Renders the game board, messages, and confirmation prompts.

    Args:
        state (dict): The current game state.
        background_color (tuple): The background color (R, G, B).
        font_color (tuple): The font color for text (R, G, B).
        highlight_color (tuple): The color for highlighted balls (R, G, B).

    Returns:
        None
    """
    if state["is_announcing"]:
        handle_announcement(state)
    elif state["is_reviewing"]:
        handle_review(state)
    else:
        handle_idle_render(state, background_color, font_color, highlight_color)


def handle_announcement(state):
    """Handles transitioning from announcement to review mode."""
    state["is_announcing"] = False
    state["is_reviewing"] = True
    state["review_start_time"] = time.time()


def handle_review(state):
    """Handles rendering the review mode and transitioning to idle."""
    display_ball_review(state)
    if time.time() - state["review_start_time"] >= REVIEW_DURATION:
        if state["current_ball"]:
            animate_ball_transition(
                start_pos=(WIDTH // 2, HEIGHT // 2),
                end_pos=get_board_position(state["current_ball"]),
                start_radius=REVIEW_CIRCLE_RADIUS,
                end_radius=CIRCLE_RADIUS,
                start_font_size=200,
                end_font_size=NUMBER_FONT_SIZE - 25,
                ball_label=state["current_ball"],
                duration=1.5,
            )
        state["is_reviewing"] = False


def handle_idle_render(state, background_color, font_color, highlight_color):
    """Handles rendering the idle board and confirmation messages."""
    clear_screen()
    display_bingo_board(state, font_color, highlight_color)
    confirmation_message = get_confirmation_message(state)
    if confirmation_message:
        display_confirmation(confirmation_message)
    pygame.display.flip()


def load_and_scale_images():
    """Load and scale pattern images with error handling."""
    images = {}
    for key, filename in pattern_filenames.items():
        try:
            img = pygame.image.load(os.path.join(script_dir, filename))
            images[key] = pygame.transform.scale(img, (450, 500))  # Resize to fit the UI
        except FileNotFoundError:
            logging.warning(f"Image file '{filename}' for pattern '{key}' not found. Falling back to text.")
            images[key] = None
        except pygame.error as e:
            logging.warning(f"Failed to load or scale image '{filename}' for pattern '{key}': {e}")
            images[key] = None
    return images


def initialize_state(pattern_images):
    """Initialize the game state dictionary."""
    return {
        "balls": initialize_balls(),
        "drawn_balls": [],
        "last_game": [],
        "awaiting_confirmation": False,
        "awaiting_undo_confirmation": False,
        "awaiting_restore_confirmation": False,
        "message_timeout": 0,
        "running": True,
        "is_announcing": False,
        "is_reviewing": False,
        "announcement_time": 0,
        "review_start_time": 0,
        "current_ball": None,
        "is_manual_mode": False,
        "current_pattern": "REGULAR",
        "pattern_images": pattern_images,
    }


def run_game_loop(state):
    """Run the main game loop."""
    logging.info("Game started.")
    while state["running"]:
        render(state, BACKGROUND_COLOR, FONT_COLOR, HIGHLIGHT_COLOR)
        handle_input(state)
        pygame.display.flip()
    logging.info("Game exited.")


def cleanup_game():
    """Clean up resources and exit the game."""
    pygame.quit()
    sys.exit()


def main():
    """Main game function to initialize and run the Bingo game."""
    # Load pattern images
    pattern_images = load_and_scale_images()

    # Initialize game state
    state = initialize_state(pattern_images)

    # Run the game loop
    run_game_loop(state)

    # Cleanup on exit
    cleanup_game()

### Run the game ###
main()
