#!/usr/bin/env python3
"""
Simple Snake Game with interactive GUI.
Use arrow keys to move. Eat the food to grow and score points. Don't hit the walls or yourself!
Features: background music, sound effects, high score, increasing speed, pause.

If you see "macOS 26 (2602) or later required" when running with `python snake_game.py`,
run instead:  ./run_snake.sh   or  pythonw snake_game.py
"""

import tkinter as tk
import random
import math
import os
import array
import io
import re
import sys
import platform
import urllib.request
from typing import Optional


def _should_enable_pygame() -> bool:
    """Determine whether importing pygame is safe and desired.

    On some macOS versions, certain pygame/SDL wheels can abort the interpreter at import
    time (not a Python exception). To keep the game playable (audio becomes a no-op), we
    skip importing pygame unless it appears compatible.

    Environment overrides:
    - SNAKE_DISABLE_PYGAME=1: Always skip pygame import.
    - SNAKE_ENABLE_PYGAME=1: Attempt pygame import even if we'd normally skip it.

    Returns:
        bool: True if pygame should be imported, False otherwise.
    """

    if os.getenv("SNAKE_DISABLE_PYGAME", "").lower() in {"1", "true", "yes"}:
        return False

    if os.getenv("SNAKE_ENABLE_PYGAME", "").lower() in {"1", "true", "yes"}:
        return True

    if sys.platform == "darwin":
        try:
            darwin_major = int(platform.release().split(".")[0])
        except Exception:
            # If we can't confidently identify the OS version, default to safety.
            return False

        # Some pygame builds abort at import time on older macOS/Darwin versions.
        # Keep the game playable by disabling audio in that case.
        if darwin_major < 26:
            return False

    return True


# Optional: pygame for background music and sound effects
if _should_enable_pygame():
    try:
        import pygame

        PYGAME_AVAILABLE = True
    except ImportError:
        pygame = None  # type: ignore[assignment]
        PYGAME_AVAILABLE = False
else:
    pygame = None  # type: ignore[assignment]
    PYGAME_AVAILABLE = False

# Optional: Pillow for loading background image (JPEG/PNG)
try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Game constants
CELL_SIZE = 24
GRID_WIDTH = 20
GRID_HEIGHT = 16
INITIAL_GAME_SPEED = 120
MIN_GAME_SPEED = 45
SPEED_UP_POINTS = 30
SPEED_UP_AMOUNT = 8
BG_COLOR = "#1a1a2e"
SNAKE_COLOR = "#00d9ff"
SNAKE_HEAD_COLOR = "#00ff88"
FOOD_COLOR = "#ff6b6b"
WALL_COLOR = "#16213e"
TEXT_COLOR = "#eaeaea"
ACCENT_COLOR = "#ffd93d"
HIGH_SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".snake_high_score")
SAMPLE_RATE = 22050
# Background image: from Havahart article (snakes in your yard)
BACKGROUND_ARTICLE_URL = "https://www.havahart.com/articles/identify-rid-poisonous-snakes-yard"
BACKGROUND_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".snake_background.jpg")
# Fallback if article image unavailable: free-use grass/yard image
FALLBACK_BG_URL = "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600"


def _fetch_background_image_url(article_url: str) -> Optional[str]:
    """Fetch article HTML and return og:image or first content image URL, or None.

    Args:
        article_url (str): URL of the HTML page to fetch and parse for an image.

    Returns:
        str | None: Absolute URL of the first suitable image found, or None on failure.
    """
    try:
        req = urllib.request.Request(article_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        # og:image
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if m:
            return m.group(1).strip()
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)
        if m:
            return m.group(1).strip()
        # First img in content
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html)
        if m:
            src = m.group(1).strip()
            if src.startswith("//"):
                return "https:" + src
            if src.startswith("/"):
                from urllib.parse import urljoin
                return urljoin(article_url, src)
            return src
    except Exception:
        pass
    return None


def _download_background_image(target_path: str, width: int, height: int) -> bool:
    """Download background image from article or fallback; save to target_path.

    Args:
        target_path (str): File path where the image will be saved (e.g. JPEG).
        width (int): Desired image width in pixels (used when Pillow is available).
        height (int): Desired image height in pixels (used when Pillow is available).

    Returns:
        bool: True if the image was successfully downloaded and saved, False otherwise.
    """
    url = _fetch_background_image_url(BACKGROUND_ARTICLE_URL)
    if not url:
        url = FALLBACK_BG_URL
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        if not PILLOW_AVAILABLE:
            with open(target_path, "wb") as f:
                f.write(data)
            return True
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGB")
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        img.save(target_path, "JPEG", quality=85)
        return True
    except Exception:
        try:
            req = urllib.request.Request(FALLBACK_BG_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            if PILLOW_AVAILABLE:
                img = Image.open(io.BytesIO(data))
                img = img.convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
                img.save(target_path, "JPEG", quality=85)
            else:
                with open(target_path, "wb") as f:
                    f.write(data)
            return True
        except Exception:
            pass
    return False


def load_high_score() -> int:
    """Load high score from file.

    Returns:
        int: The saved high score, or 0 if the file is missing or invalid.
    """
    try:
        if os.path.isfile(HIGH_SCORE_FILE):
            with open(HIGH_SCORE_FILE, "r") as f:
                return max(0, int(f.read().strip()))
    except (ValueError, OSError):
        pass
    return 0


def save_high_score(score: int) -> None:
    """Save high score to file.

    Args:
        score (int): The high score value to persist.

    Returns:
        None
    """
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(score))
    except OSError:
        pass


class GameAudio:
    """Background music and sound effects using pygame. No-op if pygame unavailable."""

    def __init__(self) -> None:
        """Initialize the audio subsystem and generate procedural music and SFX.

        Returns:
            None
        """
        self.music_playing = False
        self.sounds = {}
        if not PYGAME_AVAILABLE:
            return
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=1024)
            self._make_music()
            self._make_sounds()
        except Exception:
            pass

    def _make_music(self) -> None:
        """Generate a short looping ambient tune (chord progression).

        Populates self.bg_sound with a pygame Sound, or sets it to None on failure.

        Returns:
            None
        """
        try:
            duration_sec = 4.0
            n_samples = int(SAMPLE_RATE * duration_sec)
            t = [i / SAMPLE_RATE for i in range(n_samples)]
            f1, f2 = 110.0, 164.0
            wave = [0.15 * (math.sin(2 * math.pi * f1 * x) + 0.6 * math.sin(2 * math.pi * f2 * x)) for x in t]
            for i in range(min(400, n_samples // 2)):
                wave[i] *= i / 400
                wave[-1 - i] *= i / 400
            buf = array.array("h", (int(32767 * x) for x in wave))
            self.bg_sound = pygame.mixer.Sound(buffer=buf.tobytes())
        except Exception:
            self.bg_sound = None

    def _make_sounds(self) -> None:
        """Generate eat and game-over sounds.

        Populates self.sounds with 'eat' and 'game_over' pygame Sound objects, or clears on failure.

        Returns:
            None
        """
        try:
            n = int(SAMPLE_RATE * 0.12)
            t = [i / SAMPLE_RATE for i in range(n)]
            wave = [0.3 * math.sin(2 * math.pi * 880 * x) * math.exp(-x * 20) for x in t]
            buf = array.array("h", (int(32767 * x) for x in wave))
            self.sounds["eat"] = pygame.mixer.Sound(buffer=buf.tobytes())
            n = int(SAMPLE_RATE * 0.4)
            t = [i / SAMPLE_RATE for i in range(n)]
            freqs = [400 * (1 - 0.7 * i / n) for i in range(n)]
            wave = [0.25 * math.sin(2 * math.pi * f * x) for x, f in zip(t, freqs)]
            buf = array.array("h", (int(32767 * x) for x in wave))
            self.sounds["game_over"] = pygame.mixer.Sound(buffer=buf.tobytes())
        except Exception:
            self.sounds.clear()

    def start_music(self) -> None:
        """Start looping background music (no-op if pygame or bg_sound unavailable).

        Returns:
            None
        """
        if not PYGAME_AVAILABLE or not getattr(self, "bg_sound", None):
            return
        try:
            self.bg_sound.play(loops=-1)
            self.music_playing = True
        except Exception:
            pass

    def stop_music(self) -> None:
        """Stop all pygame mixer playback (no-op if pygame unavailable).

        Returns:
            None
        """
        if not PYGAME_AVAILABLE:
            return
        try:
            pygame.mixer.stop()
            self.music_playing = False
        except Exception:
            pass

    def play_eat(self) -> None:
        """Play the eat-food sound effect (no-op if pygame or sound unavailable).

        Returns:
            None
        """
        if not PYGAME_AVAILABLE or "eat" not in self.sounds:
            return
        try:
            self.sounds["eat"].play()
        except Exception:
            pass

    def play_game_over(self) -> None:
        """Play the game-over sound effect (no-op if pygame or sound unavailable).

        Returns:
            None
        """
        if not PYGAME_AVAILABLE or "game_over" not in self.sounds:
            return
        try:
            self.sounds["game_over"].play()
        except Exception:
            pass


class SnakeGame:
    """Main game window and loop: tkinter GUI, snake state, and input handling."""

    def __init__(self) -> None:
        """Create the main window, canvas, labels, and start the game loop.

        Returns:
            None
        """
        self.root = tk.Tk()
        self.root.title("Snake Game")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_COLOR)

        # Canvas size
        self.canvas_width = CELL_SIZE * GRID_WIDTH
        self.canvas_height = CELL_SIZE * GRID_HEIGHT

        # Title and score
        self.title_label = tk.Label(
            self.root,
            text="🐍 SNAKE",
            font=("Courier", 24, "bold"),
            fg=ACCENT_COLOR,
            bg=BG_COLOR,
        )
        self.title_label.pack(pady=(12, 4))

        self.score_label = tk.Label(
            self.root,
            text="Score: 0  •  High Score: 0",
            font=("Courier", 14),
            fg=TEXT_COLOR,
            bg=BG_COLOR,
        )
        self.score_label.pack(pady=(0, 4))
        self.high_score = load_high_score()
        self.game_speed = INITIAL_GAME_SPEED
        self.paused = False
        self.audio = GameAudio()

        # Game canvas
        self.canvas = tk.Canvas(
            self.root,
            width=self.canvas_width,
            height=self.canvas_height,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(padx=16, pady=(0, 8))

        # Background image from article URL (or fallback)
        self.bg_photo = None
        if PILLOW_AVAILABLE:
            try:
                if not os.path.isfile(BACKGROUND_CACHE):
                    _download_background_image(
                        BACKGROUND_CACHE,
                        self.canvas_width,
                        self.canvas_height,
                    )
                if os.path.isfile(BACKGROUND_CACHE):
                    img = Image.open(BACKGROUND_CACHE).convert("RGB")
                    img = img.resize((self.canvas_width, self.canvas_height), Image.Resampling.LANCZOS)
                    self.bg_photo = ImageTk.PhotoImage(img)
            except Exception:
                pass

        # Instructions
        self.inst_label = tk.Label(
            self.root,
            text="Arrow keys • Pause: P • Restart: R or Space",
            font=("Courier", 10),
            fg="#888",
            bg=BG_COLOR,
        )
        self.inst_label.pack(pady=(0, 12))

        # Game state
        self.snake = []
        self.direction = "Right"
        self.next_direction = "Right"
        self.food = None
        self.score = 0
        self.game_over = False
        self.game_started = False

        self.setup_game()
        self.bind_keys()
        self.draw()
        self.root.mainloop()

    def setup_game(self) -> None:
        """Initialize or reset the game state (snake, direction, score, food, speed).

        Returns:
            None
        """
        center_x = GRID_WIDTH // 2
        center_y = GRID_HEIGHT // 2
        self.snake = [
            (center_x - 2, center_y),
            (center_x - 1, center_y),
            (center_x, center_y),
        ]
        self.direction = "Right"
        self.next_direction = "Right"
        self.score = 0
        self.game_over = False
        self.paused = False
        self.game_speed = INITIAL_GAME_SPEED
        self.spawn_food()
        self.high_score = load_high_score()
        self._update_score_display()
        self.inst_label.config(text="Arrow keys • Pause: P • Restart: R or Space")

    def _update_score_display(self) -> None:
        """Refresh the on-screen score and high score label.

        Returns:
            None
        """
        disp = f"Score: {self.score}  •  High Score: {self.high_score}"
        self.score_label.config(text=disp)

    def draw_grid(self) -> None:
        """Draw background image (if loaded), then grid lines and border on the canvas.

        Returns:
            None
        """
        self.canvas.delete("all")
        if self.bg_photo:
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_photo)
        for x in range(0, self.canvas_width + 1, CELL_SIZE):
            self.canvas.create_line(
                x, 0, x, self.canvas_height, fill=WALL_COLOR, width=1
            )
        for y in range(0, self.canvas_height + 1, CELL_SIZE):
            self.canvas.create_line(
                0, y, self.canvas_width, y, fill=WALL_COLOR, width=1
            )
        # Border
        self.canvas.create_rectangle(
            1, 1, self.canvas_width - 1, self.canvas_height - 1,
            outline=ACCENT_COLOR, width=2
        )

    def spawn_food(self) -> None:
        """Place food at a random cell not occupied by the snake. Updates self.food.

        Returns:
            None
        """
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in self.snake:
                self.food = (x, y)
                break

    def draw_cell(
        self, x: int, y: int, color: str, outline: Optional[str] = None
    ) -> None:
        """Draw a filled rectangle for one grid cell on the canvas.

        Args:
            x (int): Grid column (0-based).
            y (int): Grid row (0-based).
            color (str): Fill color (e.g. hex string).
            outline (str | None): Outline color; defaults to color if None.

        Returns:
            None
        """
        x1 = x * CELL_SIZE + 2
        y1 = y * CELL_SIZE + 2
        x2 = x1 + CELL_SIZE - 4
        y2 = y1 + CELL_SIZE - 4
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=color,
            outline=outline or color,
            width=1,
        )

    def draw(self) -> None:
        """Redraw the full scene: grid, snake, food, and any game-over or pause overlay.

        Returns:
            None
        """
        self.draw_grid()
        if self.game_over:
            self.canvas.create_text(
                self.canvas_width // 2,
                self.canvas_height // 2,
                text="GAME OVER\nScore: " + str(self.score) + "\nPress R or Space",
                font=("Courier", 18, "bold"),
                fill=ACCENT_COLOR,
                justify="center",
            )
            return
        if self.paused:
            self.canvas.create_text(
                self.canvas_width // 2,
                self.canvas_height // 2,
                text="PAUSED\nPress P to resume",
                font=("Courier", 20, "bold"),
                fill=ACCENT_COLOR,
                justify="center",
            )
        # Food
        if self.food:
            self.draw_cell(self.food[0], self.food[1], FOOD_COLOR)
        # Snake
        for i, (x, y) in enumerate(self.snake):
            color = SNAKE_HEAD_COLOR if i == len(self.snake) - 1 else SNAKE_COLOR
            self.draw_cell(x, y, color)

    def move_snake(self) -> None:
        """Advance the snake one cell, handle food/wall/self collision, and schedule the next tick.

        Returns:
            None
        """
        if self.game_over:
            self.draw()
            self.root.after(self.game_speed, self.move_snake)
            return

        if self.paused:
            self.draw()
            self.root.after(self.game_speed, self.move_snake)
            return

        self.direction = self.next_direction
        head_x, head_y = self.snake[-1]

        if self.direction == "Up":
            head_y -= 1
        elif self.direction == "Down":
            head_y += 1
        elif self.direction == "Left":
            head_x -= 1
        else:
            head_x += 1

        # Wall collision
        if head_x < 0 or head_x >= GRID_WIDTH or head_y < 0 or head_y >= GRID_HEIGHT:
            self.game_over = True
            self.audio.stop_music()
            self.audio.play_game_over()
            if self.score > self.high_score:
                self.high_score = self.score
                save_high_score(self.high_score)
            self._update_score_display()
            self.inst_label.config(text="You hit the wall! Press R or Space to restart.")
            self.draw()
            self.root.after(self.game_speed, self.move_snake)
            return

        # Self collision
        if (head_x, head_y) in self.snake:
            self.game_over = True
            self.audio.stop_music()
            self.audio.play_game_over()
            if self.score > self.high_score:
                self.high_score = self.score
                save_high_score(self.high_score)
            self._update_score_display()
            self.inst_label.config(text="You hit yourself! Press R or Space to restart.")
            self.draw()
            self.root.after(self.game_speed, self.move_snake)
            return

        self.snake.append((head_x, head_y))

        # Food collision
        if (head_x, head_y) == self.food:
            self.score += 10
            self.audio.play_eat()
            if self.score > self.high_score:
                self.high_score = self.score
                save_high_score(self.high_score)
            self._update_score_display()
            self.spawn_food()
            # Speed up every SPEED_UP_POINTS
            if self.score % SPEED_UP_POINTS == 0 and self.score > 0:
                self.game_speed = max(MIN_GAME_SPEED, self.game_speed - SPEED_UP_AMOUNT)
        else:
            self.snake.pop(0)

        self.draw()
        self.root.after(self.game_speed, self.move_snake)

    def change_direction(self, new_dir: str) -> None:
        """Update movement direction if not opposite to current; may start the game and music.

        Args:
            new_dir (str): One of "Up", "Down", "Left", "Right".

        Returns:
            None
        """
        opposites = {
            "Up": "Down",
            "Down": "Up",
            "Left": "Right",
            "Right": "Left",
        }
        if new_dir != opposites.get(self.next_direction):
            self.next_direction = new_dir
            if not self.game_started:
                self.game_started = True
                self.audio.start_music()
                self.move_snake()

    def toggle_pause(self) -> None:
        """Toggle pause state and update the instruction label (no-op if game over or not started).

        Returns:
            None
        """
        if self.game_over or not self.game_started:
            return
        self.paused = not self.paused
        if self.paused:
            self.inst_label.config(text="Paused • Press P to resume • R or Space to restart")
        else:
            self.inst_label.config(text="Arrow keys • Pause: P • Restart: R or Space")
        self.draw()

    def restart(self) -> None:
        """Restart the game from initial state and resume the move loop.

        Returns:
            None
        """
        self.game_started = False
        self.setup_game()
        self.draw()
        self.root.after(self.game_speed, self.move_snake)

    def bind_keys(self) -> None:
        """Bind arrow keys, P (pause), R and Space (restart) to their handlers.

        Returns:
            None
        """
        self.root.bind("<Up>", lambda e: self.change_direction("Up"))
        self.root.bind("<Down>", lambda e: self.change_direction("Down"))
        self.root.bind("<Left>", lambda e: self.change_direction("Left"))
        self.root.bind("<Right>", lambda e: self.change_direction("Right"))
        self.root.bind("p", lambda e: self.toggle_pause())
        self.root.bind("P", lambda e: self.toggle_pause())
        self.root.bind("r", lambda e: self.restart())
        self.root.bind("R", lambda e: self.restart())
        self.root.bind("<space>", lambda e: self.restart())


if __name__ == "__main__":
    SnakeGame()
