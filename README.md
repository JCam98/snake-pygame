# Snake Game

## One-line value statement

A classic 2D Snake game in Python with a minimal dependency footprint: play in a GUI with optional sound and background image, high-score persistence, and constant-speed gameplay.

---

## What is this?

**What problem does this solve?**  
It provides a ready-to-run, educational implementation of the classic Snake arcade game—easy to clone, run, and modify without heavy frameworks.

**Who is this for?**  
- Learners practicing Python and simple game loops  
- Anyone wanting a quick, playable Snake with minimal setup  
- Developers looking for a reference GUI game (tkinter + optional pygame)

**Why does it exist?**  
To offer a single-file core game that works out of the box with the standard library, with optional enhancements (audio, background image) that degrade gracefully if dependencies are missing.

---

## Features

- **Classic gameplay**: Move with arrow keys; eat food to grow and score; avoid walls and your own tail.
- **Score & high score**: Current score and persistent high score (saved to a local file).
- **Constant speed**: Snake moves at a fixed speed throughout the game (no speed increase).
- **Pause**: Press **P** to pause or resume.
- **Restart**: Press **R** or **Space** to restart after game over or at any time. After restart, press an arrow key to start the move loop (same as initial game start).
- **Background music & sound effects**: Looping ambient music, eat sound, and game-over sound (requires `pygame`).
- **Optional background image**: Themed playfield image, downloaded and cached on first run (requires `Pillow` and network); falls back to solid color if unavailable.
- **Graceful fallback**: Runs with only Python and tkinter; audio and background image are optional.

---

## Tech stack

| Layer        | Technology |
|-------------|------------|
| Language    | Python 3   |
| GUI         | **tkinter** (stdlib) |
| Audio       | **pygame** (optional) – background music and SFX |
| Image       | **Pillow** (optional) – background image loading and resize |

No other frameworks or engines required.

---

## Setup & installation

1. **Clone the repository** (or download the project folder).

2. **Ensure Python 3 is installed**  
   The game uses only the standard library for core gameplay. For sound and background image, from the **repository root**:

   ```bash
   pip install -r conf/requirements.txt
   ```
   This installs optional: `pygame>=2.1.0`, `Pillow>=9.0.0`.

3. **Run the game**  
   From the repository root, run the game from the `src/` directory:

   ```bash
   cd src
   python snake_game.py
   ```
   On macOS, if you see a message like *"macOS 26 (2602) or later required"* when using `python snake_game.py`, run from `src/` either:

   ```bash
   ./run_snake.sh
   ```
   or:

   ```bash
   pythonw snake_game.py
   ```

---

## Usage example

```bash
# From repository root (snake-pygame)
cd snake-pygame
pip install -r conf/requirements.txt   # optional: sound & background image
cd src
python snake_game.py
```

- **Start**: Move with any arrow key to start the game and background music (if pygame is available). Same applies after restart—press an arrow to begin moving again.
- **Play**: Eat red food (score +10); avoid walls and your tail.
- **Pause**: **P** — **Resume**: **P** again.
- **Restart**: **R** or **Space** (after game over or anytime).

---

## Project structure

```
snake-pygame/
├── README.md
├── LICENSE
├── Dockerfile    
├── conf/
│   └── requirements.txt   # Optional deps: pygame, Pillow
├── scripts
└── src/
    ├── snake_game.py      # Main game (GUI, logic, optional audio/image)
    └── run_snake.sh       # Launcher (prefers pythonw on macOS)
```

At runtime the game may create **inside `src/`** (same directory as `snake_game.py`):

- `.snake_high_score` – persisted high score
- `.snake_background.jpg` – cached background image (if Pillow and download succeeded)

---

## Configuration

There is no external config file. All tuning is via **constants at the top of `src/snake_game.py`**:

| Constant | Default | Purpose |
|----------|---------|---------|
| `CELL_SIZE` | 24 | Pixel size of each grid cell |
| `CELL_PADDING` | 2 | Inner padding for drawn cells |
| `GRID_WIDTH` | 20 | Grid width (cells) |
| `GRID_HEIGHT` | 16 | Grid height (cells) |
| `GRID_CELLS` | 320 | Total cells (`GRID_WIDTH × GRID_HEIGHT`) |
| `INITIAL_GAME_SPEED` | 120 | Delay between moves (ms); speed is constant |
| `BG_COLOR`, `SNAKE_COLOR`, etc. | (hex) | UI colors |
| `HIGH_SCORE_FILE` | path to `.snake_high_score` | High score file path |
| `BACKGROUND_ARTICLE_URL` / `FALLBACK_BG_URL` | URLs | Source for optional background image |

Edit these and save to change grid size, speed, or colors.

---

## Limitations

- **Single player only** – no multiplayer or AI.
- **Grid and speed** – grid size and speed are fixed in code (no in-game settings).
- **Platform** – on some macOS setups, `python snake_game.py` may show a Tcl/Tk version message; from `src/` use `./run_snake.sh` or `pythonw snake_game.py` instead.
- **Background image** – requires network access on first run (or when cache is missing) and optional Pillow; falls back to solid color on failure.
- **Audio** – requires optional `pygame`; no audio if pygame is not installed or init fails.
- **High score** – stored in a file inside `src/` (not user-specific).

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) in the repository root for the full text.

---

## Design decisions

- **tkinter for GUI**: No extra install for core gameplay; works on typical Python installations (Windows, macOS, Linux).
- **Optional pygame and Pillow**: Audio and background image are optional so the game runs with minimal dependencies and fails gracefully (no crash, just no sound/image).
- **Single main file**: Core game lives in `src/snake_game.py` for simplicity and easy reading; constants at top for easy tuning.
- **Procedural audio**: Background music and SFX are generated in code (e.g. with `math.sin`) to avoid shipping or downloading asset files.
- **High score in `src/`**: `.snake_high_score` is written next to the script so the game stays self-contained when run from `src/`.
- **Shell launcher**: `src/run_snake.sh` prefers `pythonw` on macOS to avoid Tcl/Tk version dialogs when running from a terminal.
- **Constant speed and restart behavior**: Game speed stays fixed for consistency. Restart cancels any pending move callbacks and waits for the first arrow press before starting the loop, matching the initial game behavior and avoiding duplicate loops.
