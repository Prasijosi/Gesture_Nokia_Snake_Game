import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from snake_game import GameState, SnakeGame


class TestFreeMovement(unittest.TestCase):
    def setUp(self):
        self.game = SnakeGame()
        self.game.game_state = GameState.PLAYING
        self.game.camera_free_movement = True

    def tearDown(self):
        self.game.quit()

    def _cell_center_norm(self, cell):
        return (
            (cell[0] + 0.5) / self.game.grid_width,
            (cell[1] + 0.5) / self.game.grid_height,
        )

    def test_same_cell_does_not_game_over(self):
        head_cell = self.game.snake[0]
        self.game.camera_finger_pos = self._cell_center_norm(head_cell)
        self.game.update()
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.snake[0], head_cell)

    def test_moves_to_adjacent_cell(self):
        head_cell = self.game.snake[0]
        target_cell = (head_cell[0] + 1, head_cell[1])
        self.game.camera_finger_pos = self._cell_center_norm(target_cell)
        self.game.update()
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.snake[0], target_cell)


if __name__ == "__main__":
    unittest.main()
