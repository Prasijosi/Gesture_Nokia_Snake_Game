"""
Gesture recognition with MediaPipe hand tracking.
Now directly tracks the index finger tip and returns its normalized position.
Also provides directional gestures (UP/DOWN/LEFT/RIGHT) based on finger movement
for compatibility with the original control scheme.
"""

import math
import os
import urllib.request
from collections import deque
from typing import Optional, Tuple

import cv2
import numpy as np
from mediapipe import Image as MPImage, ImageFormat
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision.hand_landmarker import HandLandmarker, HandLandmarkerOptions


HAND_LANDMARKER_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)

WRIST = 0
THUMB_TIP = 4
INDEX_FINGER_TIP = 8
MIDDLE_FINGER_TIP = 12
RING_FINGER_TIP = 16
PINKY_TIP = 20

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17),
]

# Minimum movement (normalised) before a new direction is emitted
DIRECTION_THRESHOLD = 0.03


class LandmarkPoint:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z


def download_model(url: str, dest_path: str) -> bool:
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
        return True
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        urllib.request.urlretrieve(url, dest_path)
        return True
    except Exception as exc:
        print(f"Error downloading model: {exc}")
        return False


class GestureController:
    def __init__(self, smoothing_frames: int = 5):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(script_dir, "models")
        self.hand_model_path = os.path.join(models_dir, "hand_landmarker.task")

        if not download_model(HAND_LANDMARKER_MODEL_URL, self.hand_model_path):
            raise RuntimeError("Failed to prepare hand landmarker model")

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.hand_model_path),
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.5,
        )
        self.hands = HandLandmarker.create_from_options(options)

        # Smoothing for finger position
        self.finger_history: deque = deque(maxlen=smoothing_frames)

        # Direction state (for compatibility with old gesture output)
        self._last_finger_pos: Optional[Tuple[float, float]] = None
        self.current_direction: Optional[str] = None
        self.pause_cooldown = 0

        # Expose the last predicted tip for main.py
        self.last_predicted_tip: Optional[Tuple[float, float]] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _smooth_finger(self, raw_x: float, raw_y: float) -> Tuple[float, float]:
        """Apply moving average to finger coordinates."""
        self.finger_history.append((raw_x, raw_y))
        avg_x = np.mean([p[0] for p in self.finger_history])
        avg_y = np.mean([p[1] for p in self.finger_history])
        return avg_x, avg_y

    def _draw_hand_landmarks(self, frame: np.ndarray, hand_landmarks) -> None:
        h, w = frame.shape[:2]
        points = []
        for lm in hand_landmarks:
            x, y = int(lm.x * w), int(lm.y * h)
            points.append((x, y))
            cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)
        for s, e in HAND_CONNECTIONS:
            if s < len(points) and e < len(points):
                cv2.line(frame, points[s], points[e], (255, 0, 0), 2)

    def _draw_finger_cursor(self, frame: np.ndarray, finger_pos: Tuple[float, float]) -> None:
        """Draw a bright cursor at the index finger tip."""
        h, w = frame.shape[:2]
        fx, fy = int(finger_pos[0] * w), int(finger_pos[1] * h)
        cv2.circle(frame, (fx, fy), 15, (0, 255, 255), 2)
        cv2.circle(frame, (fx, fy), 5, (0, 255, 255), -1)

    def _gesture_from_finger_movement(self, finger_pos: Tuple[float, float]) -> Optional[str]:
        """
        Convert finger movement into a direction string (UP/DOWN/LEFT/RIGHT)
        for compatibility with the original gesture-based controls.
        """
        if self._last_finger_pos is None:
            self._last_finger_pos = finger_pos
            return None

        dx = finger_pos[0] - self._last_finger_pos[0]
        dy = finger_pos[1] - self._last_finger_pos[1]
        dist = math.hypot(dx, dy)

        if dist < DIRECTION_THRESHOLD:
            return self.current_direction

        # Determine dominant axis
        if abs(dx) >= abs(dy):
            direction = "RIGHT" if dx > 0 else "LEFT"
        else:
            direction = "DOWN" if dy > 0 else "UP"

        # Update last position to avoid re‑triggering the same direction
        self._last_finger_pos = finger_pos
        self.current_direction = direction
        return direction

    def _is_pinching(self, hand_landmarks) -> bool:
        thumb_tip = hand_landmarks[THUMB_TIP]
        index_tip = hand_landmarks[INDEX_FINGER_TIP]
        wrist = hand_landmarks[WRIST]
        middle_tip = hand_landmarks[MIDDLE_FINGER_TIP]
        pinch_distance = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
        hand_scale = math.hypot(wrist.x - middle_tip.x, wrist.y - middle_tip.y)
        if hand_scale < 1e-6:
            return False
        return (pinch_distance / hand_scale) < 0.28

    def _is_pause_gesture(self, hand_landmarks) -> bool:
        wrist = hand_landmarks[WRIST]
        tips = [THUMB_TIP, INDEX_FINGER_TIP, MIDDLE_FINGER_TIP, RING_FINGER_TIP, PINKY_TIP]
        tips_above = sum(1 for idx in tips if hand_landmarks[idx].y < wrist.y)
        spread = abs(hand_landmarks[THUMB_TIP].x - hand_landmarks[PINKY_TIP].x)
        return tips_above >= 4 and spread > 0.45

    # ------------------------------------------------------------------
    # Public API – returns finger position, pinch, pause, direction
    # ------------------------------------------------------------------

    def detect_gestures(self, frame: np.ndarray) -> Tuple[Optional[str], bool, np.ndarray]:
        """
        Returns:
            gesture: direction string ("UP"/"DOWN"/"LEFT"/"RIGHT"/"PAUSE") or None
            pinch: boolean (thumb and index finger touching)
            frame: annotated frame (with landmarks and cursor)
        """
        mp_image = MPImage(image_format=ImageFormat.SRGB, data=frame)
        results = self.hands.detect(mp_image)

        gesture = None
        pinch = False

        if results.hand_landmarks:
            landmarks = results.hand_landmarks[0]

            # --- Index finger tip extraction and smoothing ---
            raw_x = landmarks[INDEX_FINGER_TIP].x
            raw_y = landmarks[INDEX_FINGER_TIP].y
            smooth_x, smooth_y = self._smooth_finger(raw_x, raw_y)
            finger_pos = (smooth_x, smooth_y)
            self.last_predicted_tip = finger_pos

            # Draw finger cursor
            self._draw_finger_cursor(frame, finger_pos)

            # --- Gesture recognition (for compatibility) ---
            if self.pause_cooldown > 0:
                self.pause_cooldown -= 1

            if self._is_pause_gesture(landmarks) and self.pause_cooldown == 0:
                gesture = "PAUSE"
                self.pause_cooldown = 24
            else:
                gesture = self._gesture_from_finger_movement(finger_pos)

            pinch = self._is_pinching(landmarks)
            self._draw_hand_landmarks(frame, landmarks)

        else:
            # No hand – reset state
            self.finger_history.clear()
            self._last_finger_pos = None
            self.current_direction = None
            self.pause_cooldown = 0
            self.last_predicted_tip = None

        return gesture, pinch, frame

    def reset_gesture_state(self):
        self.finger_history.clear()
        self._last_finger_pos = None
        self.current_direction = None
        self.pause_cooldown = 0
        self.last_predicted_tip = None

    def close(self):
        if hasattr(self, "hands") and self.hands is not None:
            self.hands.close()