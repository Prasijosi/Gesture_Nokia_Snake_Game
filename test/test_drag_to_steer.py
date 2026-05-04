import unittest

from gesture_tracking import DragToSteerTracker, DRAG_THRESHOLD, HAND_ABSENCE_FRAMES


class TestDragToSteerTracker(unittest.TestCase):
    def test_anchor_set_on_first_frame(self):
        tracker = DragToSteerTracker()
        self.assertIsNone(tracker._anchor)
        tracker.update((0.5, 0.5))
        self.assertIsNotNone(tracker._anchor)

    def test_small_drag_does_not_commit(self):
        tracker = DragToSteerTracker()
        tracker.update((0.5, 0.5))
        direction = tracker.update((0.5 + DRAG_THRESHOLD * 0.4, 0.5))
        self.assertIsNone(direction)

    def test_drag_right_commits_right(self):
        tracker = DragToSteerTracker()
        tracker.update((0.3, 0.5))
        direction = tracker.update((0.3 + DRAG_THRESHOLD * 2.5, 0.5))
        self.assertEqual(direction, "RIGHT")

    def test_drag_up_commits_up(self):
        tracker = DragToSteerTracker()
        tracker.update((0.5, 0.5))
        direction = tracker.update((0.5, 0.5 - DRAG_THRESHOLD * 2.5))
        self.assertEqual(direction, "UP")

    def test_dominant_axis_vertical(self):
        tracker = DragToSteerTracker()
        tracker.update((0.5, 0.5))
        direction = tracker.update((0.5 + DRAG_THRESHOLD * 1.2, 0.5 + DRAG_THRESHOLD * 2.4))
        self.assertEqual(direction, "DOWN")

    def test_anchor_slides_forward(self):
        tracker = DragToSteerTracker()
        tracker.update((0.5, 0.5))
        ax_before, _ = tracker._anchor
        tracker.update((0.5 + DRAG_THRESHOLD * 3.0, 0.5))
        ax_after, _ = tracker._anchor
        self.assertGreater(ax_after, ax_before)

    def test_anchor_resets_after_absence(self):
        tracker = DragToSteerTracker()
        tracker.update((0.4, 0.4))
        for _ in range(HAND_ABSENCE_FRAMES):
            tracker.update(None)
        self.assertIsNone(tracker._anchor)

    def test_anchor_not_reset_before_absence(self):
        tracker = DragToSteerTracker()
        tracker.update((0.4, 0.4))
        for _ in range(max(1, HAND_ABSENCE_FRAMES - 1)):
            tracker.update(None)
        self.assertIsNotNone(tracker._anchor)

    def test_new_anchor_after_reset(self):
        tracker = DragToSteerTracker()
        tracker.update((0.2, 0.2))
        for _ in range(HAND_ABSENCE_FRAMES):
            tracker.update(None)
        tracker.update((0.8, 0.8))
        ax, ay = tracker._anchor
        self.assertAlmostEqual(ax, 0.8, delta=0.05)
        self.assertAlmostEqual(ay, 0.8, delta=0.05)


if __name__ == "__main__":
    unittest.main()
