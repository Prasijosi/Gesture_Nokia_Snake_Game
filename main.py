import threading
import time
import cv2
import pygame
from gesture_controller import GestureController
from latency_reporter import LatencyReporter
from snake_game import GameState, SnakeGame

ENABLE_CAMERA_FREE_MOVEMENT = False
CAMERA_SLEEP_SEC = 0.002


class GameManager:
    def __init__(self):
        self.game = SnakeGame()
        self.gesture_controller = GestureController()
        self.cap = None
        self.running = True
        self.gesture_thread = None
        self.camera_enabled = False

        self.latency_reporter = LatencyReporter()
        self.last_input_time = None
        self.input_lock = threading.Lock()

        # Gesture state shared with the game loop.
        self.current_gesture = None
        self.is_speed_boost = False
        self.camera_fps = 0.0
        self.current_finger = None

    def initialize_camera(self) -> bool:
        """Initialize webcam for gesture input."""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Warning: Could not open webcam. Continuing with keyboard + mouse controls.")
            self.cap = None
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return True

    def gesture_detection_loop(self):
        """Read webcam frames and update current gesture state."""
        previous_frame_time = time.time()
        while self.running and self.cap is not None:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            gesture, pinch, annotated_frame = self.gesture_controller.detect_gestures(frame)

            # also store the predicted fingertip (normalised 0..1)
            self.current_finger = getattr(self.gesture_controller, "last_predicted_tip", None)

            with self.input_lock:
                if self.current_finger is None:
                    self.last_input_time = None
                else:
                    self.last_input_time = time.perf_counter()

            now = time.time()
            dt = max(1e-6, now - previous_frame_time)
            previous_frame_time = now
            self.camera_fps = 1.0 / dt

            self.current_gesture = gesture
            self.is_speed_boost = pinch

            cv2.imshow("Nokia Snake - Gesture Control", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.running = False
                break

            time.sleep(CAMERA_SLEEP_SEC)

    def run(self):
        """Main application loop."""
        self.camera_enabled = self.initialize_camera()

        if self.camera_enabled:
            self.gesture_thread = threading.Thread(target=self.gesture_detection_loop, daemon=True)
            self.gesture_thread.start()
            # default to drag-to-steer unless explicitly enabled
            self.game.camera_free_movement = ENABLE_CAMERA_FREE_MOVEMENT

        print("Nokia Snake Game Started")
        print("Mouse: menu and buttons")
        print("Keyboard: arrows during gameplay")
        print("Gesture: hand direction during gameplay, pinch for speed boost")

        last_update = time.time()

        while self.running:
            now = time.time()

            for event in pygame.event.get():
                action = self.game.process_event(event)
                if action == "quit":
                    self.running = False

            # pass finger position for optional free movement
            self.game.set_runtime_stats(self.camera_fps, self.current_gesture, self.current_finger)

            if self.camera_enabled:
                with self.input_lock:
                    last_input = self.last_input_time
                input_age_ms = None
                if last_input is not None:
                    input_age_ms = max(0.0, (time.perf_counter() - last_input) * 1000.0)
                self.latency_reporter.record(self.camera_fps, input_age_ms)

            if self.game.game_state == GameState.PLAYING:
                if self.current_gesture:
                    self.game.handle_gesture(self.current_gesture)

                self.game.set_speed_boost(self.camera_enabled and self.is_speed_boost)

                step_interval = 1.0 / self.game.get_current_speed()
                if now - last_update >= step_interval:
                    self.game.update()
                    last_update = now

            self.game.draw()
            self.game.clock.tick(60)

        self.cleanup()

    def cleanup(self):
        """Release resources cleanly."""
        self.running = False

        if self.gesture_thread and self.gesture_thread.is_alive():
            self.gesture_thread.join(timeout=1.0)

        if self.cap is not None:
            self.cap.release()

        self.gesture_controller.close()
        self.latency_reporter.finalize()
        cv2.destroyAllWindows()
        self.game.quit()


def main():
    try:
        manager = GameManager()
        manager.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as exc:
        print(f"An error occurred: {exc}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
