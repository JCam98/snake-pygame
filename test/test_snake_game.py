"""Unit tests for the Snake game.

This test suite focuses on the file-based high score helpers.
"""

from __future__ import annotations

import builtins
import sys
from pathlib import Path

import pytest

# Ensure `snake_game.py` (located in ../src/) is importable when running pytest from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import snake_game  # noqa: E402


def _write_text(path: Path, text: str) -> None:
    """Write UTF-8 text to a file, creating parent directories as needed.

    Args:
        path (Path): Destination file path.
        text (str): Text content to write.

    Returns:
        None
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_load_high_score_returns_0_when_file_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Expected case: missing file returns 0."""

    hs_path = tmp_path / "missing_high_score"
    monkeypatch.setattr(snake_game, "HIGH_SCORE_FILE", str(hs_path))

    assert snake_game.load_high_score() == 0


def test_load_high_score_loads_valid_integer_with_whitespace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Expected case: parses a valid integer, ignoring surrounding whitespace."""

    hs_path = tmp_path / "high_score"
    _write_text(hs_path, "  42\n")
    monkeypatch.setattr(snake_game, "HIGH_SCORE_FILE", str(hs_path))

    assert snake_game.load_high_score() == 42


def test_load_high_score_clamps_negative_values_to_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Edge case: negative values are clamped to 0 via max(0, score)."""

    hs_path = tmp_path / "high_score"
    _write_text(hs_path, "-7")
    monkeypatch.setattr(snake_game, "HIGH_SCORE_FILE", str(hs_path))

    assert snake_game.load_high_score() == 0


def test_load_high_score_returns_0_for_empty_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failure case: empty or whitespace-only file content returns 0."""

    hs_path = tmp_path / "high_score"
    _write_text(hs_path, "\n\t\r")
    monkeypatch.setattr(snake_game, "HIGH_SCORE_FILE", str(hs_path))

    assert snake_game.load_high_score() == 0


def test_load_high_score_returns_0_when_open_raises_oserror(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failure case: OS errors while reading return 0 (e.g., permission issues)."""

    hs_path = tmp_path / "high_score"
    _write_text(hs_path, "99")
    monkeypatch.setattr(snake_game, "HIGH_SCORE_FILE", str(hs_path))

    # Force the read path and simulate an I/O error.
    monkeypatch.setattr(snake_game.os.path, "isfile", lambda _p: True)

    def _raise_oserror(*_args: object, **_kwargs: object) -> object:
        """Raise an OSError for open()."""

        raise OSError("simulated open failure")

    monkeypatch.setattr(builtins, "open", _raise_oserror)

    assert snake_game.load_high_score() == 0


def test_save_high_score_writes_to_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Expected case: save_high_score writes the provided integer as text."""

    hs_path = tmp_path / "high_score"
    monkeypatch.setattr(snake_game, "HIGH_SCORE_FILE", str(hs_path))

    snake_game.save_high_score(123)

    assert hs_path.read_text(encoding="utf-8") == "123"


def test_save_high_score_swallows_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    """Failure case: save_high_score ignores write errors."""

    def _raise_oserror(*_args: object, **_kwargs: object) -> object:
        """Raise an OSError for open()."""

        raise OSError("simulated write failure")

    monkeypatch.setattr(builtins, "open", _raise_oserror)

    # Should not raise.
    snake_game.save_high_score(5)


class _DummyResponse:
    """Context manager-like response for urllib.request.urlopen()."""

    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        """Return the response bytes."""

        return self._data

    def __enter__(self) -> "_DummyResponse":
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _tb: object | None,
    ) -> bool:
        return False


def test_fetch_background_image_url_prefers_og_image_property(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Expected case: returns og:image content when meta property exists."""

    html = b"""
    <html><head>
      <meta property='og:image' content='https://example.com/a.jpg'>
    </head></html>
    """

    monkeypatch.setattr(
        snake_game.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _DummyResponse(html),
    )

    assert (
        snake_game._fetch_background_image_url("https://example.com/article")
        == "https://example.com/a.jpg"
    )


def test_fetch_background_image_url_handles_img_src_variants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Edge case: falls back to first <img> and normalizes protocol-relative and root-relative URLs."""

    # protocol-relative
    html = b"<html><img src='//cdn.example.com/x.png'></html>"
    monkeypatch.setattr(
        snake_game.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _DummyResponse(html),
    )
    assert (
        snake_game._fetch_background_image_url("https://example.com/article")
        == "https://cdn.example.com/x.png"
    )

    # root-relative
    html2 = b"<html><img src='/assets/y.png'></html>"
    monkeypatch.setattr(
        snake_game.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _DummyResponse(html2),
    )
    assert (
        snake_game._fetch_background_image_url("https://example.com/blog/post")
        == "https://example.com/assets/y.png"
    )

    # absolute
    html3 = b"<html><img src='https://images.example.com/z.png'></html>"
    monkeypatch.setattr(
        snake_game.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _DummyResponse(html3),
    )
    assert (
        snake_game._fetch_background_image_url("https://example.com/anything")
        == "https://images.example.com/z.png"
    )


def test_fetch_background_image_url_parses_og_image_when_attributes_reversed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Edge case: supports meta tags where content appears before property."""

    html = b"""
    <html><head>
      <meta content='https://example.com/reversed.jpg' property='og:image'>
    </head></html>
    """

    monkeypatch.setattr(
        snake_game.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _DummyResponse(html),
    )

    assert (
        snake_game._fetch_background_image_url("https://example.com/article")
        == "https://example.com/reversed.jpg"
    )


def test_fetch_background_image_url_returns_none_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Failure case: network/parse errors result in None."""

    def _raise(*_args: object, **_kwargs: object) -> object:
        """Raise an exception to simulate a fetch failure."""

        raise RuntimeError("boom")

    monkeypatch.setattr(snake_game.urllib.request, "urlopen", _raise)

    assert snake_game._fetch_background_image_url("https://example.com/article") is None


def test_download_background_image_writes_bytes_when_pillow_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Expected case: when Pillow is unavailable, download writes raw bytes to disk."""

    target = tmp_path / "bg.jpg"
    monkeypatch.setattr(snake_game, "PILLOW_AVAILABLE", False)
    monkeypatch.setattr(snake_game, "_fetch_background_image_url", lambda _u: "https://x/img")
    monkeypatch.setattr(
        snake_game.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _DummyResponse(b"JPEGDATA"),
    )

    assert snake_game._download_background_image(str(target), width=10, height=10) is True
    assert target.read_bytes() == b"JPEGDATA"


def test_download_background_image_resizes_and_saves_when_pillow_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Expected case: when Pillow is available, downloads, resizes, and saves a JPEG."""

    class _DummyImg:
        """Pillow Image stub."""

        def convert(self, _mode: str) -> "_DummyImg":
            return self

        def resize(self, _size: tuple[int, int], _resample: object) -> "_DummyImg":
            return self

        def save(self, path: str, _fmt: str, **_kwargs: object) -> None:
            Path(path).write_bytes(b"SAVED")

    class _DummyImageModule:
        """Module-like stub for PIL.Image."""

        class Resampling:
            """Stub enum container."""

            LANCZOS = object()

        @staticmethod
        def open(_fp: object) -> _DummyImg:
            return _DummyImg()

    target = tmp_path / "bg.jpg"
    monkeypatch.setattr(snake_game, "PILLOW_AVAILABLE", True)
    monkeypatch.setattr(snake_game, "Image", _DummyImageModule)
    monkeypatch.setattr(snake_game, "_fetch_background_image_url", lambda _u: "https://x/img")
    monkeypatch.setattr(
        snake_game.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _DummyResponse(b"IMGBYTES"),
    )

    assert snake_game._download_background_image(str(target), width=10, height=10) is True
    assert target.read_bytes() == b"SAVED"


def test_download_background_image_uses_fallback_after_primary_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Edge case: if the primary download fails, a fallback attempt is made."""

    target = tmp_path / "bg.jpg"
    monkeypatch.setattr(snake_game, "PILLOW_AVAILABLE", False)
    monkeypatch.setattr(snake_game, "_fetch_background_image_url", lambda _u: "https://primary/img")

    calls = {"n": 0}

    def _urlopen(*_args: object, **_kwargs: object) -> _DummyResponse:
        """Fail once, then succeed."""

        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("primary failed")
        return _DummyResponse(b"FALLBACK")

    monkeypatch.setattr(snake_game.urllib.request, "urlopen", _urlopen)

    assert snake_game._download_background_image(str(target), width=10, height=10) is True
    assert target.read_bytes() == b"FALLBACK"


def test_download_background_image_returns_false_when_all_downloads_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failure case: returns False if both primary and fallback downloads error."""

    target = tmp_path / "bg.jpg"
    monkeypatch.setattr(snake_game, "PILLOW_AVAILABLE", False)
    monkeypatch.setattr(snake_game, "_fetch_background_image_url", lambda _u: None)

    def _raise(*_args: object, **_kwargs: object) -> object:
        """Raise an exception to simulate download failure."""

        raise OSError("download failed")

    monkeypatch.setattr(snake_game.urllib.request, "urlopen", _raise)

    assert snake_game._download_background_image(str(target), width=10, height=10) is False
    assert not target.exists()


class _DummySound:
    """pygame.mixer.Sound stub."""

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        self.play_calls: list[dict[str, object]] = []

    def play(self, *args: object, **kwargs: object) -> None:
        """Record sound playback."""

        self.play_calls.append({"args": args, "kwargs": kwargs})


class _DummyMixer:
    """pygame.mixer stub."""

    def __init__(self) -> None:
        self.init_calls: list[dict[str, object]] = []
        self.stop_calls = 0

    def init(self, **kwargs: object) -> None:
        """Record initialization."""

        self.init_calls.append(dict(kwargs))

    def stop(self) -> None:
        """Record stop calls."""

        self.stop_calls += 1

    def Sound(self, *_args: object, **_kwargs: object) -> _DummySound:  # noqa: N802
        """Return a new dummy sound."""

        return _DummySound()


class _DummyPygame:
    """Minimal pygame stub implementing only what GameAudio uses."""

    def __init__(self) -> None:
        self.mixer = _DummyMixer()


def test_game_audio_noops_when_pygame_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expected case: all audio methods no-op if pygame is unavailable."""

    monkeypatch.setattr(snake_game, "PYGAME_AVAILABLE", False)

    audio = snake_game.GameAudio()

    audio.start_music()
    audio.play_eat()
    audio.play_game_over()
    audio.stop_music()

    assert audio.music_playing is False
    assert audio.sounds == {}


def test_game_audio_uses_pygame_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expected case: with pygame available, initializes mixer and plays sounds."""

    dummy_pygame = _DummyPygame()
    monkeypatch.setattr(snake_game, "PYGAME_AVAILABLE", True)
    monkeypatch.setattr(snake_game, "pygame", dummy_pygame)

    audio = snake_game.GameAudio()
    assert dummy_pygame.mixer.init_calls, "mixer.init should be called"

    # Start/stop music.
    audio.start_music()
    assert audio.music_playing is True
    audio.stop_music()
    assert dummy_pygame.mixer.stop_calls == 1

    # Sound effects.
    audio.play_eat()
    audio.play_game_over()


def test_game_audio_start_music_noops_without_bg_sound(monkeypatch: pytest.MonkeyPatch) -> None:
    """Edge case: start_music is a no-op if bg_sound was not created."""

    dummy_pygame = _DummyPygame()
    monkeypatch.setattr(snake_game, "PYGAME_AVAILABLE", True)
    monkeypatch.setattr(snake_game, "pygame", dummy_pygame)

    audio = snake_game.GameAudio()
    audio.bg_sound = None

    audio.start_music()
    assert audio.music_playing is False


def test_game_audio_sound_methods_noop_when_sound_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Edge case: play_eat / play_game_over no-op if the sound keys aren't present."""

    dummy_pygame = _DummyPygame()
    monkeypatch.setattr(snake_game, "PYGAME_AVAILABLE", True)
    monkeypatch.setattr(snake_game, "pygame", dummy_pygame)

    audio = snake_game.GameAudio()
    audio.sounds = {}

    audio.play_eat()
    audio.play_game_over()


def test_game_audio_swallows_init_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Failure case: exceptions during pygame init are swallowed."""

    dummy_pygame = _DummyPygame()

    def _raise(**_kwargs: object) -> None:
        """Raise to simulate init failure."""

        raise RuntimeError("init failed")

    dummy_pygame.mixer.init = _raise  # type: ignore[method-assign]

    monkeypatch.setattr(snake_game, "PYGAME_AVAILABLE", True)
    monkeypatch.setattr(snake_game, "pygame", dummy_pygame)

    audio = snake_game.GameAudio()
    assert audio.sounds == {}
    assert audio.music_playing is False


class _DummyLabel:
    """tk.Label stub capturing config calls."""

    def __init__(self) -> None:
        self.config_calls: list[dict[str, object]] = []

    def config(self, **kwargs: object) -> None:
        """Record configuration updates."""

        self.config_calls.append(dict(kwargs))


class _DummyCanvas:
    """tk.Canvas stub capturing drawing calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def delete(self, *args: object, **kwargs: object) -> None:
        """Record delete calls."""

        self.calls.append(("delete", args, dict(kwargs)))

    def create_line(self, *args: object, **kwargs: object) -> None:
        """Record line creations."""

        self.calls.append(("create_line", args, dict(kwargs)))

    def create_rectangle(self, *args: object, **kwargs: object) -> None:
        """Record rectangle creations."""

        self.calls.append(("create_rectangle", args, dict(kwargs)))

    def create_text(self, *args: object, **kwargs: object) -> None:
        """Record text creations."""

        self.calls.append(("create_text", args, dict(kwargs)))

    def create_image(self, *args: object, **kwargs: object) -> None:
        """Record image creations."""

        self.calls.append(("create_image", args, dict(kwargs)))


def test_dummy_canvas_records_calls() -> None:
    """Expected case: _DummyCanvas records method name, args, and kwargs for each draw call."""

    canvas = _DummyCanvas()

    canvas.delete("all")
    canvas.create_line(1, 2, 3, 4, fill="red", width=2)
    canvas.create_rectangle(1, 2, 3, 4, fill="blue")
    canvas.create_text(10, 20, text="hello", font=("Courier", 12))
    canvas.create_image(0, 0, anchor="nw", image=object())

    assert [name for name, _args, _kwargs in canvas.calls] == [
        "delete",
        "create_line",
        "create_rectangle",
        "create_text",
        "create_image",
    ]
    assert canvas.calls[1][1] == (1, 2, 3, 4)
    assert canvas.calls[1][2] == {"fill": "red", "width": 2}


class _DummyRoot:
    """tk.Tk stub capturing bindings and scheduled callbacks."""

    def __init__(self) -> None:
        self.bind_calls: list[tuple[str, object]] = []
        self.after_calls: list[tuple[int, object]] = []

    def bind(self, sequence: str, func: object) -> None:
        """Record bind calls."""

        self.bind_calls.append((sequence, func))

    def after(self, delay_ms: int, func: object) -> None:
        """Record scheduled callbacks without executing them."""

        self.after_calls.append((delay_ms, func))


class _DummyAudio:
    """Audio stub for SnakeGame tests."""

    def __init__(self) -> None:
        self.start_music_calls = 0
        self.stop_music_calls = 0
        self.play_eat_calls = 0
        self.play_game_over_calls = 0

    def start_music(self) -> None:
        """Record music starts."""

        self.start_music_calls += 1

    def stop_music(self) -> None:
        """Record music stops."""

        self.stop_music_calls += 1

    def play_eat(self) -> None:
        """Record eat SFX."""

        self.play_eat_calls += 1

    def play_game_over(self) -> None:
        """Record game-over SFX."""

        self.play_game_over_calls += 1


def _make_game() -> snake_game.SnakeGame:
    """Create a SnakeGame instance without invoking its tkinter-heavy __init__.

    Returns:
        SnakeGame: A partially-initialized game object suitable for unit tests.
    """

    game = snake_game.SnakeGame.__new__(snake_game.SnakeGame)
    game.root = _DummyRoot()
    game.canvas = _DummyCanvas()
    game.score_label = _DummyLabel()
    game.inst_label = _DummyLabel()
    game.audio = _DummyAudio()
    game.bg_photo = None

    game.canvas_width = 48
    game.canvas_height = 48

    game.snake = [(1, 1), (2, 1), (3, 1)]
    game.direction = "Right"
    game.next_direction = "Right"
    game.food = (5, 5)
    game.score = 0
    game.high_score = 0
    game.game_speed = snake_game.INITIAL_GAME_SPEED
    game.paused = False
    game.game_over = False
    game.game_started = True

    return game


def test_snake_game_update_score_display_sets_label_text() -> None:
    """Expected case: _update_score_display writes formatted score/high score."""

    game = _make_game()
    game.score = 7
    game.high_score = 9

    game._update_score_display()

    assert game.score_label.config_calls
    assert game.score_label.config_calls[-1]["text"] == "Score: 7  •  High Score: 9"


def test_snake_game_draw_grid_draws_border_and_optional_bg() -> None:
    """Expected case: draw_grid clears canvas and draws border; draws bg when available."""

    game = _make_game()

    game.draw_grid()
    assert any(name == "delete" for name, _args, _kwargs in game.canvas.calls)
    assert any(name == "create_rectangle" for name, _args, _kwargs in game.canvas.calls)
    assert not any(name == "create_image" for name, _args, _kwargs in game.canvas.calls)

    game.canvas.calls.clear()
    game.bg_photo = object()
    game.draw_grid()
    assert any(name == "create_image" for name, _args, _kwargs in game.canvas.calls)


def test_snake_game_draw_cell_calls_create_rectangle() -> None:
    """Expected case: draw_cell computes cell coordinates and draws a rectangle."""

    game = _make_game()

    game.draw_cell(1, 2, color="#fff")

    rect_calls = [c for c in game.canvas.calls if c[0] == "create_rectangle"]
    assert rect_calls


def test_snake_game_draw_variants_game_over_paused_and_normal() -> None:
    """Expected case: draw renders game-over overlay, paused overlay, and normal scene."""

    game = _make_game()

    # game over overlay returns early
    game.game_over = True
    game.draw()
    assert any(name == "create_text" for name, _args, _kwargs in game.canvas.calls)

    # paused overlay
    game.canvas.calls.clear()
    game.game_over = False
    game.paused = True
    game.draw()
    assert any(name == "create_text" for name, _args, _kwargs in game.canvas.calls)

    # normal scene
    game.canvas.calls.clear()
    game.paused = False
    game.food = (1, 1)
    game.snake = [(0, 0), (1, 0)]
    game.draw()
    assert any(name == "create_rectangle" for name, _args, _kwargs in game.canvas.calls)


def test_snake_game_spawn_food_avoids_snake_cells(monkeypatch: pytest.MonkeyPatch) -> None:
    """Edge case: spawn_food retries until it finds a free cell."""

    game = _make_game()
    game.snake = [(0, 0)]

    seq = [0, 0, 1, 1]

    def _randint(_a: int, _b: int) -> int:
        """Return deterministic values from seq."""

        return seq.pop(0)

    monkeypatch.setattr(snake_game.random, "randint", _randint)

    game.spawn_food()
    assert game.food == (1, 1)


def test_snake_game_change_direction_starts_game_and_prevents_reverse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Expected case: change_direction prevents immediate reversal and starts on first valid input."""

    game = _make_game()
    game.game_started = False
    game.next_direction = "Right"

    called = {"move": 0}

    def _move_stub() -> None:
        """Record move_snake invocations."""

        called["move"] += 1

    monkeypatch.setattr(game, "move_snake", _move_stub)

    # Opposite direction should be ignored.
    game.change_direction("Left")
    assert game.next_direction == "Right"
    assert game.game_started is False

    # Valid direction should start the game.
    game.change_direction("Up")
    assert game.next_direction == "Up"
    assert game.game_started is True
    assert game.audio.start_music_calls == 1
    assert called["move"] == 1


def test_snake_game_toggle_pause_noops_when_game_over_or_not_started() -> None:
    """Edge case: toggle_pause is a no-op when game over or before game starts."""

    game = _make_game()
    game.game_over = True
    game.toggle_pause()
    assert game.paused is False

    game.game_over = False
    game.game_started = False
    game.toggle_pause()
    assert game.paused is False


def test_snake_game_toggle_pause_toggles_state_and_updates_label() -> None:
    """Expected case: toggles paused state and updates instructions."""

    game = _make_game()
    game.game_started = True

    game.toggle_pause()
    assert game.paused is True
    assert game.inst_label.config_calls

    game.toggle_pause()
    assert game.paused is False


def test_snake_game_restart_calls_setup_draw_and_schedules_next_tick(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Expected case: restart resets game_started and schedules move loop."""

    game = _make_game()

    called = {"setup": 0, "draw": 0, "move": 0}

    def _setup_stub() -> None:
        """Record setup_game."""

        called["setup"] += 1

    def _draw_stub() -> None:
        """Record draw."""

        called["draw"] += 1

    def _move_stub() -> None:
        """Record move_snake."""

        called["move"] += 1

    monkeypatch.setattr(game, "setup_game", _setup_stub)
    monkeypatch.setattr(game, "draw", _draw_stub)
    monkeypatch.setattr(game, "move_snake", _move_stub)

    game.game_started = True
    game.restart()

    assert game.game_started is False
    assert called["setup"] == 1
    assert called["draw"] == 1
    assert game.root.after_calls


def test_snake_game_bind_keys_binds_expected_sequences() -> None:
    """Expected case: bind_keys registers key handlers on root."""

    game = _make_game()
    game.bind_keys()

    sequences = {seq for seq, _func in game.root.bind_calls}
    assert "<Up>" in sequences
    assert "<Down>" in sequences
    assert "<Left>" in sequences
    assert "<Right>" in sequences
    assert "p" in sequences
    assert "P" in sequences
    assert "r" in sequences
    assert "R" in sequences
    assert "<space>" in sequences


def test_snake_game_setup_game_resets_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expected case: setup_game resets snake, direction, score, and reloads high score."""

    game = _make_game()
    game.game_started = True

    monkeypatch.setattr(game, "spawn_food", lambda: setattr(game, "food", (2, 2)))
    monkeypatch.setattr(snake_game, "load_high_score", lambda: 101)

    called = {"update": 0}

    def _update_stub() -> None:
        """Record score display updates."""

        called["update"] += 1

    monkeypatch.setattr(game, "_update_score_display", _update_stub)

    game.setup_game()

    assert game.score == 0
    assert game.game_over is False
    assert game.paused is False
    assert game.food == (2, 2)
    assert game.high_score == 101
    assert called["update"] == 1


def test_snake_game_move_snake_noops_when_game_over(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expected case: when game_over, move_snake redraws and schedules next tick."""

    game = _make_game()
    game.game_over = True

    called = {"draw": 0}

    def _draw_stub() -> None:
        """Record draw call."""

        called["draw"] += 1

    monkeypatch.setattr(game, "draw", _draw_stub)

    game.move_snake()

    assert called["draw"] == 1
    assert game.root.after_calls


def test_snake_game_move_snake_noops_when_paused(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expected case: when paused, move_snake redraws and schedules next tick."""

    game = _make_game()
    game.paused = True

    called = {"draw": 0}

    def _draw_stub() -> None:
        """Record draw call."""

        called["draw"] += 1

    monkeypatch.setattr(game, "draw", _draw_stub)

    game.move_snake()

    assert called["draw"] == 1
    assert game.root.after_calls


def test_snake_game_move_snake_wall_collision_sets_game_over(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Failure case: wall collision ends the game and persists a new high score."""

    game = _make_game()
    game.snake = [(snake_game.GRID_WIDTH - 1, 0)]
    game.direction = "Right"
    game.next_direction = "Right"
    game.score = 50
    game.high_score = 10

    saved: list[int] = []

    monkeypatch.setattr(snake_game, "save_high_score", lambda s: saved.append(s))
    monkeypatch.setattr(game, "draw", lambda: None)

    game.move_snake()

    assert game.game_over is True
    assert game.audio.stop_music_calls == 1
    assert game.audio.play_game_over_calls == 1
    assert game.high_score == 50
    assert saved == [50]


def test_snake_game_move_snake_game_over_does_not_save_when_not_high_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Edge case: on game over, high score is only saved when the score exceeds it."""

    game = _make_game()
    game.snake = [(snake_game.GRID_WIDTH - 1, 0)]
    game.direction = "Right"
    game.next_direction = "Right"
    game.score = 5
    game.high_score = 10

    saved: list[int] = []

    monkeypatch.setattr(snake_game, "save_high_score", lambda s: saved.append(s))
    monkeypatch.setattr(game, "draw", lambda: None)

    game.move_snake()

    assert game.game_over is True
    assert game.high_score == 10
    assert saved == []


def test_snake_game_move_snake_self_collision_sets_game_over(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Failure case: self collision ends the game and can persist a new high score."""

    game = _make_game()
    # Move Up from head (2, 2) into (2, 1), which is already part of the snake.
    game.snake = [(2, 1), (2, 2)]
    game.direction = "Up"
    game.next_direction = "Up"
    game.score = 20
    game.high_score = 0

    saved: list[int] = []

    monkeypatch.setattr(snake_game, "save_high_score", lambda s: saved.append(s))
    monkeypatch.setattr(game, "draw", lambda: None)

    game.move_snake()

    assert game.game_over is True
    assert game.audio.stop_music_calls == 1
    assert game.audio.play_game_over_calls == 1
    assert game.high_score == 20
    assert saved == [20]


def test_snake_game_move_snake_food_collision_increases_score_and_speedups(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Expected case: eating food grows snake, updates score, spawns new food, and can speed up."""

    game = _make_game()
    game.snake = [(0, 0), (1, 0)]
    game.direction = "Right"
    game.next_direction = "Right"

    # Force a speed-up on this eat: score goes from 20 -> 30.
    game.score = 20
    game.high_score = 0

    # Place food at next head position.
    game.food = (2, 0)

    spawned = {"count": 0}

    def _spawn() -> None:
        """Record spawn_food calls."""

        spawned["count"] += 1
        game.food = (9, 9)

    saved: list[int] = []

    monkeypatch.setattr(game, "spawn_food", _spawn)
    monkeypatch.setattr(snake_game, "save_high_score", lambda s: saved.append(s))
    monkeypatch.setattr(game, "draw", lambda: None)

    old_speed = game.game_speed
    game.move_snake()

    assert game.score == 30
    assert game.audio.play_eat_calls == 1
    assert game.high_score == 30
    assert saved == [30]
    assert spawned["count"] == 1
    assert len(game.snake) == 3, "snake should grow when eating"
    assert game.game_speed < old_speed


def test_snake_game_move_snake_normal_move_pops_tail(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expected case: normal move advances the snake by one and keeps length constant."""

    game = _make_game()
    game.snake = [(0, 0), (1, 0)]
    game.direction = "Right"
    game.next_direction = "Right"
    game.food = (9, 9)

    monkeypatch.setattr(game, "draw", lambda: None)

    game.move_snake()

    assert game.snake == [(1, 0), (2, 0)]


def test_snake_game_move_snake_updates_direction_from_next_direction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Expected case: move_snake copies next_direction into direction each tick."""

    game = _make_game()
    game.snake = [(1, 1)]
    game.direction = "Right"
    game.next_direction = "Down"
    game.food = (9, 9)

    monkeypatch.setattr(game, "draw", lambda: None)

    game.move_snake()

    assert game.direction == "Down"
