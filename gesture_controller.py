"""
Gesture Recognition Module for Nokia Snake Game
Handles hand tracking and gesture detection using MediaPipe Tasks API
Compatible with MediaPipe 0.10.0+
"""

import cv2
import numpy as np
import os
import urllib.request
from typing import Tuple, Optional

# Import MediaPipe Tasks API
from mediapipe.tasks.python.vision.hand_landmarker import HandLandmarker, HandLandmarkerOptions
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe import Image as MPImage, ImageFormat


# Model download URL
HAND_LANDMARKER_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"

# Hand landmark indices (same as MediaPipe HandLandmark enum)
WRIST = 0
THUMB_TIP = 4
INDEX_FINGER_TIP = 8
MIDDLE_FINGER_TIP = 12
RING_FINGER_TIP = 16
PINKY_TIP = 20

# Hand connections for drawing
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),  # Index finger
    (0, 9), (9, 10), (10, 11), (11, 12),  # Middle finger
    (0, 13), (13, 14), (14, 15), (15, 16),  # Ring finger
    (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
    (5, 9), (9, 13), (13, 17)  # Palm
]


def download_model(url: str, dest_path: str) -> bool:
    """Download a model file if it doesn't exist."""
    if os.path.exists(dest_path):
        # Check if file is valid (not empty or placeholder)
        if os.path.getsize(dest_path) > 1000:  # Valid model files are larger than 1KB
            return True
    
    print(f"Downloading model to {dest_path}...")
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        urllib.request.urlretrieve(url, dest_path)
        print(f"Model downloaded successfully!")
        return True
    except Exception as e:
        print(f"Error downloading model: {e}")
        return False


class GestureController:
    def __init__(self):
        """Initialize MediaPipe Tasks hand detection"""
        # Get the directory where this script is located
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.models_dir = os.path.join(self.script_dir, "models")
        
        # Model paths
        self.hand_model_path = os.path.join(self.models_dir, "hand_landmarker.task")
        
        # Download models if needed
        if not download_model(HAND_LANDMARKER_MODEL_URL, self.hand_model_path):
            raise RuntimeError("Failed to download hand landmarker model. Please check your internet connection.")
        
        # Initialize hand landmarker
        self.hand_options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.hand_model_path),
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5
        )
        self.hands = HandLandmarker.create_from_options(self.hand_options)
        
        # Gesture state tracking
        self.previous_position = None
        self.gesture_threshold = 0.05
        self.current_direction = None
        self.gesture_cooldown = 0
        self.max_cooldown = 10
        
    def _draw_hand_landmarks(self, frame: np.ndarray, hand_landmarks) -> None:
        """Draw hand landmarks and connections on the frame."""
        h, w = frame.shape[:2]
        points = []
        
        # Draw landmarks
        for lm in hand_landmarks:
            x = int(lm.x * w)
            y = int(lm.y * h)
            points.append((x, y))
            cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)
        
        # Draw connections
        for connection in HAND_CONNECTIONS:
            start_idx, end_idx = connection
            if start_idx < len(points) and end_idx < len(points):
                cv2.line(frame, points[start_idx], points[end_idx], (255, 0, 0), 2)
    
    def detect_gestures(self, frame: np.ndarray) -> Tuple[Optional[str], bool, np.ndarray]:
        """
        Detect hand gestures and return direction and pinch state
        
        Args:
            frame: Input video frame (BGR format)
            
        Returns:
            Tuple of (direction, is_pinching, annotated_frame)
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image
        mp_image = MPImage(image_format=ImageFormat.SRGB, data=rgb_frame)
        
        # Process hands
        hand_results = self.hands.detect(mp_image)
        
        # Create annotated frame
        annotated_frame = frame.copy()
        
        direction = None
        is_pinching = False
        
        # Process hand landmarks
        if hand_results.hand_landmarks:
            for hand_landmarks in hand_results.hand_landmarks:
                # Draw hand landmarks
                self._draw_hand_landmarks(annotated_frame, hand_landmarks)
                
                # Get hand center position (wrist)
                wrist = hand_landmarks[WRIST]
                current_pos = np.array([wrist.x, wrist.y])
                
                # Detect swipe gestures
                if self.previous_position is not None and self.gesture_cooldown <= 0:
                    movement = current_pos - self.previous_position
                    
                    # Check for significant movement
                    if np.linalg.norm(movement) > self.gesture_threshold:
                        if abs(movement[0]) > abs(movement[1]):
                            # Horizontal movement
                            if movement[0] > 0:
                                direction = "RIGHT"
                            else:
                                direction = "LEFT"
                        else:
                            # Vertical movement
                            if movement[1] > 0:
                                direction = "DOWN"
                            else:
                                direction = "UP"
                        
                        if direction != self.current_direction:
                            self.current_direction = direction
                            self.gesture_cooldown = self.max_cooldown
                
                # Detect pinch gesture (thumb and index finger close)
                thumb_tip = hand_landmarks[THUMB_TIP]
                index_tip = hand_landmarks[INDEX_FINGER_TIP]
                
                thumb_pos = np.array([thumb_tip.x, thumb_tip.y])
                index_pos = np.array([index_tip.x, index_tip.y])
                
                distance = np.linalg.norm(thumb_pos - index_pos)
                is_pinching = distance < 0.05
                
                # Draw pinch indicator
                if is_pinching:
                    cv2.putText(annotated_frame, "SPEED BOOST!", (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                
                self.previous_position = current_pos
        
        # Update cooldown
        if self.gesture_cooldown > 0:
            self.gesture_cooldown -= 1
        
        # Display current direction
        if self.current_direction:
            cv2.putText(annotated_frame, f"Direction: {self.current_direction}", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
        return self.current_direction, is_pinching, annotated_frame
    
    def reset_gesture_state(self):
        """Reset gesture detection state"""
        self.previous_position = None
        self.current_direction = None
        self.gesture_cooldown = 0
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'hands') and self.hands:
            self.hands.close()