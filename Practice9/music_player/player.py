"""
player.py — Core MusicPlayer logic
Handles playlist management, playback state, and track metadata.
"""

import os
import time
import pygame


class Track:
    """Represents a single audio track with metadata."""

    def __init__(self, filepath: str, index: int):
        self.filepath = filepath
        self.index = index
        self.filename = os.path.basename(filepath)
        # Derive a display title from the filename (strip extension, clean underscores)
        name, _ = os.path.splitext(self.filename)
        self.title = name.replace("_", " ").replace("-", " ").title()
        self.duration = self._get_duration()

    def _get_duration(self) -> float:
        """Read WAV duration without pygame using the wave module."""
        try:
            import wave as wave_mod
            with wave_mod.open(self.filepath, "r") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
        except Exception:
            return 0.0

    @property
    def duration_str(self) -> str:
        mins = int(self.duration) // 60
        secs = int(self.duration) % 60
        return f"{mins:02d}:{secs:02d}"

    def __repr__(self):
        return f"Track({self.index + 1}: '{self.title}' [{self.duration_str}])"


class MusicPlayer:
    """
    Manages playlist state and pygame.mixer playback.

    States
    ------
    STOPPED  — mixer idle, position reset
    PLAYING  — mixer actively playing
    PAUSED   — mixer paused (pos saved)
    """

    STOPPED = "STOPPED"
    PLAYING = "PLAYING"
    PAUSED  = "PAUSED"

    def __init__(self, music_dir: str):
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        self.playlist: list[Track] = []
        self.current_index: int = 0
        self.state: str = self.STOPPED
        self._play_start_time: float = 0.0   # wall-clock when current track began
        self._pause_offset: float = 0.0      # seconds already played before pause
        self.volume: float = 0.8
        pygame.mixer.music.set_volume(self.volume)

        self._load_playlist(music_dir)

    # ------------------------------------------------------------------
    # Playlist helpers
    # ------------------------------------------------------------------

    def _load_playlist(self, music_dir: str) -> None:
        """Scan *music_dir* for supported audio files and build the playlist."""
        supported = (".wav", ".mp3", ".ogg", ".flac")
        if not os.path.isdir(music_dir):
            raise FileNotFoundError(f"Music directory not found: {music_dir}")

        files = sorted(
            f for f in os.listdir(music_dir)
            if os.path.splitext(f)[1].lower() in supported
        )
        self.playlist = [
            Track(os.path.join(music_dir, f), i) for i, f in enumerate(files)
        ]
        if not self.playlist:
            raise RuntimeError(f"No audio files found in: {music_dir}")

    @property
    def current_track(self) -> Track:
        return self.playlist[self.current_index]

    @property
    def track_count(self) -> int:
        return len(self.playlist)

    # ------------------------------------------------------------------
    # Playback controls
    # ------------------------------------------------------------------

    def play(self) -> None:
        """Play (or resume) the current track."""
        if self.state == self.PLAYING:
            return  # already playing

        if self.state == self.PAUSED:
            pygame.mixer.music.unpause()
            # Restore elapsed-time accounting
            self._play_start_time = time.monotonic() - self._pause_offset
            self.state = self.PLAYING
            return

        # STOPPED — load and start fresh
        pygame.mixer.music.load(self.current_track.filepath)
        pygame.mixer.music.play()
        self._play_start_time = time.monotonic()
        self._pause_offset = 0.0
        self.state = self.PLAYING

    def stop(self) -> None:
        """Stop playback and reset position."""
        pygame.mixer.music.stop()
        self.state = self.STOPPED
        self._pause_offset = 0.0

    def pause(self) -> None:
        """Pause if playing; resume if paused."""
        if self.state == self.PLAYING:
            pygame.mixer.music.pause()
            self._pause_offset = self.elapsed_seconds
            self.state = self.PAUSED
        elif self.state == self.PAUSED:
            self.play()   # delegates to unpause branch

    def next_track(self) -> None:
        """Advance to the next track (wraps around)."""
        was_playing = self.state == self.PLAYING
        self.stop()
        self.current_index = (self.current_index + 1) % self.track_count
        if was_playing:
            self.play()

    def prev_track(self) -> None:
        """Go back to the previous track (wraps around)."""
        was_playing = self.state == self.PLAYING
        self.stop()
        self.current_index = (self.current_index - 1) % self.track_count
        if was_playing:
            self.play()

    def volume_up(self, step: float = 0.1) -> None:
        self.volume = min(1.0, self.volume + step)
        pygame.mixer.music.set_volume(self.volume)

    def volume_down(self, step: float = 0.1) -> None:
        self.volume = max(0.0, self.volume - step)
        pygame.mixer.music.set_volume(self.volume)

    # ------------------------------------------------------------------
    # Progress / position
    # ------------------------------------------------------------------

    @property
    def elapsed_seconds(self) -> float:
        """Seconds elapsed in the current track."""
        if self.state == self.PLAYING:
            elapsed = time.monotonic() - self._play_start_time
            return min(elapsed, self.current_track.duration or elapsed)
        if self.state == self.PAUSED:
            return self._pause_offset
        return 0.0

    @property
    def progress(self) -> float:
        """Progress as a 0.0–1.0 fraction."""
        dur = self.current_track.duration
        if dur <= 0:
            return 0.0
        return min(self.elapsed_seconds / dur, 1.0)

    @property
    def elapsed_str(self) -> str:
        secs = int(self.elapsed_seconds)
        return f"{secs // 60:02d}:{secs % 60:02d}"

    # ------------------------------------------------------------------
    # Auto-advance
    # ------------------------------------------------------------------

    def tick(self) -> None:
        """
        Call once per frame.
        Automatically advances to the next track when the current one ends.
        """
        if self.state == self.PLAYING and not pygame.mixer.music.get_busy():
            # Track finished naturally → advance
            self.stop()
            self.current_index = (self.current_index + 1) % self.track_count
            self.play()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def quit(self) -> None:
        self.stop()
        pygame.mixer.quit()
