import math
from typing import Optional, Tuple

DRAG_THRESHOLD = 0.05
ANCHOR_SLIDE_FRACTION = 0.35
HAND_ABSENCE_FRAMES = 3


def ema_alpha_from_frames(frames: int) -> float:
    if frames <= 1:
        return 1.0
    alpha = 2.0 / (frames + 1.0)
    return max(0.4, min(0.8, alpha))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


class DragToSteerTracker:
    def __init__(
        self,
        drag_threshold: float = DRAG_THRESHOLD,
        anchor_slide_fraction: float = ANCHOR_SLIDE_FRACTION,
        absence_frames: int = HAND_ABSENCE_FRAMES,
        ema_alpha: float = 0.4,
    ):
        self.drag_threshold = max(0.001, float(drag_threshold))
        self.anchor_slide_fraction = max(0.0, min(1.0, float(anchor_slide_fraction)))
        self.absence_frames = max(1, int(absence_frames))
        self.ema_alpha = max(0.05, min(0.95, float(ema_alpha)))

        self._anchor: Optional[Tuple[float, float]] = None
        self._smooth_pos: Optional[Tuple[float, float]] = None
        self._absent_frames = 0
        self.current_direction: Optional[str] = None

    def reset(self):
        self._anchor = None
        self._smooth_pos = None
        self._absent_frames = 0
        self.current_direction = None

    def _apply_ema(self, raw_pos: Tuple[float, float]) -> Tuple[float, float]:
        if self._smooth_pos is None:
            self._smooth_pos = raw_pos
            return raw_pos

        sx = self.ema_alpha * raw_pos[0] + (1.0 - self.ema_alpha) * self._smooth_pos[0]
        sy = self.ema_alpha * raw_pos[1] + (1.0 - self.ema_alpha) * self._smooth_pos[1]
        self._smooth_pos = (sx, sy)
        return self._smooth_pos

    def get_smoothed_pos(self) -> Optional[Tuple[float, float]]:
        return self._smooth_pos

    def update(self, raw_pos: Optional[Tuple[float, float]]) -> Optional[str]:
        if raw_pos is None:
            self._absent_frames += 1
            if self._absent_frames >= self.absence_frames:
                self.reset()
            return None

        self._absent_frames = 0
        clamped = (_clamp01(raw_pos[0]), _clamp01(raw_pos[1]))
        smooth_pos = self._apply_ema(clamped)

        if self._anchor is None:
            self._anchor = smooth_pos
            return None

        dx = smooth_pos[0] - self._anchor[0]
        dy = smooth_pos[1] - self._anchor[1]

        if abs(dx) < self.drag_threshold and abs(dy) < self.drag_threshold:
            return self.current_direction

        if abs(dx) >= abs(dy):
            direction = "RIGHT" if dx > 0 else "LEFT"
            slide = min(abs(dx), self.drag_threshold * self.anchor_slide_fraction)
            self._anchor = (_clamp01(self._anchor[0] + math.copysign(slide, dx)), self._anchor[1])
        else:
            direction = "DOWN" if dy > 0 else "UP"
            slide = min(abs(dy), self.drag_threshold * self.anchor_slide_fraction)
            self._anchor = (self._anchor[0], _clamp01(self._anchor[1] + math.copysign(slide, dy)))

        self.current_direction = direction
        return direction
