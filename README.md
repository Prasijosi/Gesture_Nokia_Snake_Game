# 🐍 Nokia Snake Game - Gesture Control

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green.svg)](https://opencv.org)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10+-orange.svg)](https://mediapipe.dev)
[![Pygame](https://img.shields.io/badge/Pygame-2.5+-blue.svg)](https://pygame.org)
[![Numpy](https://img.shields.io/badge/Numpy-1.24+-blue.svg)](https://numpy.org)


**Created by Prashiddha Joshi**

A classic Nokia Snake game controlled by hand gestures via webcam using MediaPipe and OpenCV. Experience the nostalgia of Nokia Snake with modern AI-powered gesture recognition!

## Features

### Classic Nokia Snake Game
- **Authentic Nokia-style graphics** with green monochrome theme
- **Grid-based movement** with rectangular snake segments
- **Growing snake** mechanics - snake grows when eating fruit
- **Collision detection** - game ends when hitting walls or self
- **Score tracking** - earn points by eating fruit
- **Smooth animations** with particle effects

### Hand Gesture Controls
- **MediaPipe hand tracking** for real-time gesture recognition
- **Swipe & Drag-to-steer** - intuitive drag-to-steer tracking with proportional EMA smoothing to control snake direction
- **Pinch gesture** - bring thumb and index finger together for speed boost
- **Visual feedback** - see hand landmarks and current direction
- **Automatic model download** - required ML models are downloaded on first run

### Dual Window Interface
- **Game Window** - Classic Nokia Snake gameplay
- **Gesture Window** - Live webcam feed with hand tracking visualization

## Quick Start

### 1. Install Dependencies
Run the setup script to automatically install all required packages:
```bash
python setup.py
```

Or install manually:
```bash
pip install -r requirements.txt
```

### 2. Run the Game
```bash
python main.py
```

## Requirements

- **Python 3.8+**
- **Webcam** (built-in or external)
- **Internet connection** (for first-time model download)
- **Required packages:**
  - opencv-python >= 4.8.0
  - mediapipe >= 0.10.0 (uses Tasks API)
  - numpy >= 1.24.0
  - pygame >= 2.5.0

## Controls

### Hand Gestures
| Gesture | Action |
|---------|--------|
| **Swipe Up** | Move snake up |
| **Swipe Down** | Move snake down |
| **Swipe Left** | Move snake left |
| **Swipe Right** | Move snake right |
| **Pinch** (thumb + index) | Speed boost |

### Game Controls
- **ESC** - Quit game
- **Show UP gesture** when game over - Restart game
- **Q** in gesture window - Quit

## Game Content & Mechanics

### Game Modes & Maps
- **Classic**: The original Nokia snake experience with an open map.
- **Time Attack**: Race against the clock to eat as many fruits as possible.
- **Obstacle**: Navigate around randomly placed static obstacles that block your path.
- **Maze**: Challenge yourself in a predefined maze map with complex wall layouts.

### Custom Skins
- Cycle between different visual aesthetics in the main menu:
  - **Classic**: The nostalgic Nokia green monochrome.
  - **Neon**: Bright, vibrant cyber-style neon colors.
  - **Ice**: Cool blue, frosty color palette.

### Immersive Audio
Interactive sound effects are included in the `sounds/` directory:
- **Eating Fruit**: `eat_fruit.wav` / `eatfruit.mp3`
- **Game Over**: `game_over.wav` / `GameOver.mp3`
- **Power Up / Menu**: `button_click.wav` / `GameStart.mp3`
(Sound can be toggled on/off from the main menu)

### Snake Behavior & Rules
- **Movement**: Snake moves continuously in the current direction. Cannot move directly backward.
- **Speed Boost**: Speed increases when a pinch gesture is detected.
- **Growth**: Snake grows by one segment and earns **+10 points** per fruit eaten.
- **Game Over**: Triggered when hitting wall boundaries or colliding with its own body. Show an **UP gesture** to restart.

## File Structure

```
nokia-snake-gesture-control/
├── main.py                 # Main game entry point
├── setup.py                # Automatic dependency installer
├── requirements.txt        # Python package dependencies
├── README.md               # This file
└── snake_game/             # Core game logic and UI
    ├── game/               # Game engine and core mechanics
    │   └── core.py
    ├── control/            # Hand gesture recognition and tracking
    │   ├── gesture_controller.py
    │   └── gesture_tracking.py
    ├── ui/                 # UI management and overlays
    │   └── ui_manager.py
    ├── utils/              # Utility classes (latency reporting)
    │   └── latency_reporter.py
    ├── sounds/             # Sound assets
    └── models/             # Auto-downloaded ML models
```

## Technical Details

### Game Engine
- **Pygame** for game graphics and window management
- **Grid-based movement** (20x20 pixel grid cells)
- **60 FPS** display refresh rate
- **Variable game speed** (8-15 FPS based on difficulty)

### Computer Vision
- **MediaPipe Tasks API** for hand landmark detection (0.10.0+)
- **OpenCV** for video capture and processing
- **Real-time gesture analysis** with movement thresholds
- **Automatic model management** - downloads required models on first run

### Architecture
- **Threaded design** - game and gesture detection run in parallel
- **Modular code** - separate packages for `game` logic, `control` tracking, `ui` management, and `utils`
- **Event-driven** - gestures trigger game state changes
- **Performance monitoring** - automatic latency and FPS tracking written to `latency_reports/`

## Troubleshooting

### Camera Issues
```
Error: Could not open webcam
```
- Ensure webcam is connected and not used by other applications
- Try changing camera index in `cv2.VideoCapture(0)` to `1` or `2`
- Check camera permissions in your OS settings

### Package Installation Issues
```
Failed to install package
```
- Update pip: `python -m pip install --upgrade pip`
- Install packages individually: `pip install opencv-python`
- Use virtual environment to avoid conflicts

### Performance Issues
- **Low FPS**: Close other applications using the camera
- **Gesture lag**: Ensure good lighting and clear hand visibility
- **Game stuttering**: Lower the game resolution in `snake_game.py`

## Customization

### Adjust Gesture Sensitivity
In `snake_game/control/gesture_tracking.py`, modify:
```python
DRAG_THRESHOLD = 0.05  # Lower = more sensitive
```

### Change Game Speed
In `snake_game/game/core.py`, modify:
```python
self.base_speed = 8      # Normal speed (FPS)
self.boost_speed = 15    # Boost speed (FPS)
```

### Modify Colors
In `snake_game/game/core.py`, change color constants:
```python
self.NOKIA_GREEN = (155, 188, 15)  # Snake body color
self.LIGHT_GREEN = (204, 255, 51)  # Snake head color
```

## Development

### Adding New Gestures
1. Extend `detect_gestures()` in `snake_game/control/gesture_controller.py`
2. Add gesture recognition logic using MediaPipe landmarks
3. Return new gesture type in the function
4. Handle new gesture in `main.py` game loop

### Modifying Game Mechanics
1. Edit game logic in `snake_game/game/core.py`
2. Add new features to the `SnakeGame` class
3. Update the drawing methods for visual changes

### Testing
Automated tests are available for the gesture tracking algorithms and core game logic.
- Run tests: `python -m unittest discover test/`
- `test_drag_to_steer.py`: Verifies anchor setting, directional commits, and threshold handling.
- `test_free_movement.py`: Validates the optional camera free movement coordinates and bounds.

### Performance Metrics
The game logs input latency and camera FPS into `latency_reports/`. Review these to monitor game responsiveness.


## Credits

- **MediaPipe** by Google for hand tracking
- **OpenCV** for computer vision capabilities  
- **Pygame** for game development framework
- Inspired by the classic **Nokia Snake** game

---


**Enjoy playing Nokia Snake with hand gestures !**
