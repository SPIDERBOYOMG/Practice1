# 🎵 PyPlayer — Keyboard-Controlled Music Player

A retro-terminal-style music player built with **Python + pygame**.  
Control everything from the keyboard — no mouse required.

---

## Project Structure

```
Practice7/
└── music_player/
    ├── main.py          ← UI, event loop, keyboard handling
    ├── player.py        ← MusicPlayer & Track classes
    ├── music/
    │   ├── track1.wav   ← C major arpeggio (generated)
    │   ├── track2.wav   ← G sine wave (generated)
    │   ├── track3.wav   ← E minor arpeggio (generated)
    │   └── track4.wav   ← Bass drone (generated)
    └── README.md
```

---

## Requirements

```bash
pip install pygame
```

Python 3.10+ recommended (uses `list[Track]` type hints).

---

## Running the Player

```bash
cd Practice7/music_player
python main.py
```

---

## Keyboard Controls

| Key          | Action                        |
|-------------|-------------------------------|
| `P`          | Play / Resume                 |
| `S`          | Stop (reset position)         |
| `Space`      | Pause / Resume toggle         |
| `N`          | Next track                    |
| `B`          | Previous (Back) track         |
| `↑` or `+`   | Volume up (+10%)              |
| `↓` or `-`   | Volume down (−10%)            |
| `Q` / `Esc`  | Quit                          |

---

## Adding Your Own Music

Drop any `.wav`, `.mp3`, `.ogg`, or `.flac` file into the `music/` folder.  
The player scans the directory on startup and builds the playlist automatically — no config needed.

---

## Architecture

### `player.py` — `MusicPlayer` class

| Method/Property     | Description                                  |
|--------------------|----------------------------------------------|
| `play()`            | Start or resume playback                     |
| `stop()`            | Stop and reset position                      |
| `pause()`           | Toggle pause/resume                          |
| `next_track()`      | Advance playlist index, continue if playing  |
| `prev_track()`      | Go back, continue if playing                 |
| `volume_up/down()`  | ±10% volume, clamped to [0, 1]               |
| `tick()`            | Must be called each frame — handles auto-advance |
| `elapsed_seconds`   | Seconds played in current track              |
| `progress`          | Playback progress as 0.0–1.0 float           |

### `main.py` — UI

- **Header** — title + track counter  
- **Now Playing** — colour-coded album art placeholder, track name, state badge  
- **Waveform** — animated bar display that reacts to play/pause/stop states  
- **Progress bar** — elapsed / total time with playhead knob  
- **Volume indicator** — compact vertical bar + percentage  
- **Playlist** — scrollable list, active track highlighted  
- **Keyboard hints** — always-visible control reference  
- **Toast notifications** — fade-out confirmations for every key action  

---

## Concepts Demonstrated

- `pygame.mixer` for audio loading and playback  
- Object-oriented playlist + track management  
- Real-time elapsed-time tracking with pause compensation  
- Event-driven keyboard input mapping  
- Custom UI drawing with `pygame.draw` primitives  
- Animated waveform bars using `math.sin` + wall-clock time  
