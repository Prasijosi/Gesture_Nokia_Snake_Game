"""
Gesture recognition with MediaPipe hand tracking.
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
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (0, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (0, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (5, 9),
    (9, 13),
    (13, 17),
]


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
    def __init__(self):
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

        self.gesture_threshold = 0.08
        self.current_direction = None
        self.gesture_cooldown = 0
        self.max_cooldown = 6

        self.landmark_history = deque(maxlen=5)

    def _draw_hand_landmarks(self, frame: np.ndarray, hand_landmarks) -> None:
        h, w = frame.shape[:2]
        points = []

        for landmark in hand_landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            points.append((x, y))
            cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)

        for start_idx, end_idx in HAND_CONNECTIONS:
            if start_idx < len(points) and end_idx < len(points):
                cv2.line(frame, points[start_idx], points[end_idx], (255, 0, 0), 2)

    def _smooth_landmarks(self):
        if not self.landmark_history:
            return []

        count = len(self.landmark_history[0])
        smoothed = []

        for i in range(count):
            x = float(np.mean([sample[i].x for sample in self.landmark_history]))
            y = float(np.mean([sample[i].y for sample in self.landmark_history]))
            z = float(np.mean([sample[i].z for sample in self.landmark_history]))
            smoothed.append(LandmarkPoint(x, y, z))

        return smoothed

    def _get_gesture(self, hand_landmarks) -> Optional[str]:
        if not hand_landmarks:
            return None

        wrist = hand_landmarks[WRIST]
        index_tip = hand_landmarks[INDEX_FINGER_TIP]

        dx = index_tip.x - wrist.x
        dy = index_tip.y - wrist.y

        candidate = None
        if abs(dx) > abs(dy):
            if dx > self.gesture_threshold:
                candidate = "RIGHT"
            elif dx < -self.gesture_threshold:
                candidate = "LEFT"
        else:
            if dy > self.gesture_threshold:
                candidate = "DOWN"
            elif dy < -self.gesture_threshold:
                candidate = "UP"

        if candidate is None:
            return None

        if candidate != self.current_direction:
            if self.gesture_cooldown > 0:
                self.gesture_cooldown -= 1
                return None

            self.current_direction = candidate
            self.gesture_cooldown = self.max_cooldown
            return candidate

        if self.gesture_cooldown > 0:
            self.gesture_cooldown -= 1

        return candidate

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

    def detect_gestures(self, frame: np.ndarray) -> Tuple[Optional[str], bool, np.ndarray]:
        mp_image = MPImage(image_format=ImageFormat.SRGB, data=frame)
        results = self.hands.detect(mp_image)

        gesture = None
        pinch = False

        if results.hand_landmarks:
            landmarks = results.hand_landmarks[0]
            self.landmark_history.append(landmarks)

            if len(self.landmark_history) >= 2:
                smooth = self._smooth_landmarks()
            else:
                smooth = landmarks

            gesture = self._get_gesture(smooth)
            pinch = self._is_pinching(smooth)
            self._draw_hand_landmarks(frame, smooth)
        else:
            self.landmark_history.clear()
            self.current_direction = None
            self.gesture_cooldown = 0

        return gesture, pinch, frame

    def reset_gesture_state(self):
        self.current_direction = None
        self.gesture_cooldown = 0
        self.landmark_history.clear()

    def close(self):
        if hasattr(self, "hands") and self.hands is not None:
            self.hands.close()
