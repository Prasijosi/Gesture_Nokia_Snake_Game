import os
import random
from enum import Enum
from typing import Optional
import pygame
from ui_manager import UIManager

class GameState(Enum):
    MAIN_MENU = 1
    SETTINGS = 2
    PLAYING = 3
    GAME_OVER = 4


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class SnakeGame:
    def __init__(self, width: int = 640, height: int = 640):
        self.width = width
        self.height = height
        self.grid_size = 20
        self.grid_width = self.width // self.grid_size
        self.grid_height = self.height // self.grid_size

        self.BLACK = (10, 16, 10)
        self.WHITE = (235, 245, 220)
        self.NOKIA_GREEN = (155, 188, 15)
        self.DARK_GREEN = (90, 120, 10)
        self.LIGHT_GREEN = (190, 220, 40)
        self.RED = (224, 62, 54)
        self.ORANGE = (244, 154, 37)
        self.GRID_COLOR = (44, 68, 10)

        pygame.init()
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except pygame.error:
                pass

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Nokia Snake - Gesture Control")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.Font(None, 38)
        self.small_font = pygame.font.Font(None, 26)

        self.ui_manager = UIManager(self.width, self.height)

        self.base_speed = 8
        self.boost_speed = 14
        self.speed_boost = False

        self.sound_enabled = True
        self.master_volume = 0.6
        self.eat_sound = self._load_sound("eatfruit.mp3")
        self.game_over_sound = self._load_sound("GameOver.mp3")
        self.apply_sound_volume()

        self.game_state = GameState.MAIN_MENU
        self.particles = []
        self.reset_game()

    def _load_sound(self, filename: str) -> Optional[pygame.mixer.Sound]:
        if pygame.mixer.get_init() is None:
            return None

        sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", filename)
        if not os.path.exists(sound_path):
            return None

        if os.path.getsize(sound_path) < 44:
            return None

        try:
            return pygame.mixer.Sound(sound_path)
        except pygame.error:
            return None

    def apply_sound_volume(self):
        level = self.master_volume if self.sound_enabled else 0.0

        if self.eat_sound is not None:
            self.eat_sound.set_volume(level)
        if self.game_over_sound is not None:
            self.game_over_sound.set_volume(level)

        self.ui_manager.set_master_volume(self.master_volume)
        self.ui_manager.set_sound_enabled(self.sound_enabled)

    def set_master_volume(self, volume: float):
        self.master_volume = max(0.0, min(1.0, volume))
        self.apply_sound_volume()

    def reset_game(self):
        center_x = self.grid_width // 2
        center_y = self.grid_height // 2

        self.snake = [
            (center_x, center_y),
            (center_x - 1, center_y),
            (center_x - 2, center_y),
        ]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT

        self.score = 0
        self.game_over = False
        self.game_over_sound_played = False
        self.speed_boost = False
        self.particles = []

        self.spawn_fruit()

    def spawn_fruit(self):
        while True:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            if (x, y) not in self.snake:
                self.fruit = (x, y)
                return

    def process_event(self, event):
        if event.type == pygame.QUIT:
            return "quit"

        if self.game_state == GameState.MAIN_MENU:
            action = self.ui_manager.handle_main_menu_event(event)
            if action == "start":
                self.reset_game()
                self.game_state = GameState.PLAYING
            elif action == "settings":
                self.game_state = GameState.SETTINGS
            elif action == "quit":
                return "quit"

        elif self.game_state == GameState.SETTINGS:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game_state = GameState.MAIN_MENU
                return None

            action = self.ui_manager.handle_settings_event(event)
            if action == "back":
                self.game_state = GameState.MAIN_MENU
            elif action == "volume_changed":
                self.set_master_volume(self.ui_manager.master_volume)
            elif action == "sound_toggled":
                self.sound_enabled = self.ui_manager.sound_enabled
                self.apply_sound_volume()

        elif self.game_state == GameState.GAME_OVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game_state = GameState.MAIN_MENU
                return None

            action = self.ui_manager.handle_game_over_event(event)
            if action == "restart":
                self.reset_game()
                self.game_state = GameState.PLAYING
            elif action == "main_menu":
                self.game_state = GameState.MAIN_MENU

        elif self.game_state == GameState.PLAYING:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game_state = GameState.MAIN_MENU
                elif event.key == pygame.K_UP:
                    self._set_next_direction(Direction.UP)
                elif event.key == pygame.K_DOWN:
                    self._set_next_direction(Direction.DOWN)
                elif event.key == pygame.K_LEFT:
                    self._set_next_direction(Direction.LEFT)
                elif event.key == pygame.K_RIGHT:
                    self._set_next_direction(Direction.RIGHT)

        return None

    def _set_next_direction(self, new_direction: Direction):
        opposite = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }

        if new_direction != opposite[self.direction]:
            self.next_direction = new_direction

    def handle_gesture(self, gesture: str):
        mapping = {
            "UP": Direction.UP,
            "DOWN": Direction.DOWN,
            "LEFT": Direction.LEFT,
            "RIGHT": Direction.RIGHT,
        }

        new_direction = mapping.get(gesture)
        if new_direction is not None and self.game_state == GameState.PLAYING:
            self._set_next_direction(new_direction)

    def set_speed_boost(self, boost: bool):
        self.speed_boost = bool(boost)

    def get_current_speed(self) -> int:
        return self.boost_speed if self.speed_boost else self.base_speed

    def add_particle_effect(self, x: int, y: int):
        for _ in range(10):
            self.particles.append(
                {
                    "x": x * self.grid_size + self.grid_size // 2,
                    "y": y * self.grid_size + self.grid_size // 2,
                    "vx": random.uniform(-2.8, 2.8),
                    "vy": random.uniform(-2.8, 2.8),
                    "life": 24,
                    "max_life": 24,
                }
            )

    def update_particles(self):
        for particle in self.particles[:]:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["life"] -= 1
            if particle["life"] <= 0:
                self.particles.remove(particle)

    def update(self):
        if self.game_state != GameState.PLAYING or self.game_over:
            return

        self.direction = self.next_direction

        head_x, head_y = self.snake[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)

        wall_hit = (
            new_head[0] < 0
            or new_head[0] >= self.grid_width
            or new_head[1] < 0
            or new_head[1] >= self.grid_height
        )
        body_hit = new_head in self.snake

        if wall_hit or body_hit:
            self.game_over = True
            self.game_state = GameState.GAME_OVER
            if not self.game_over_sound_played and self.sound_enabled and self.game_over_sound is not None:
                self.game_over_sound.play()
                self.game_over_sound_played = True
            return

        self.snake.insert(0, new_head)

        if new_head == self.fruit:
            self.score += 10
            self.add_particle_effect(new_head[0], new_head[1])
            self.spawn_fruit()
            if self.sound_enabled and self.eat_sound is not None:
                self.eat_sound.play()
        else:
            self.snake.pop()

        self.update_particles()

    def _draw_grid(self):
        for x in range(0, self.width, self.grid_size):
            pygame.draw.line(self.screen, self.GRID_COLOR, (x, 0), (x, self.height))
        for y in range(0, self.height, self.grid_size):
            pygame.draw.line(self.screen, self.GRID_COLOR, (0, y), (self.width, y))

    def _draw_snake(self):
        for index, (x, y) in enumerate(self.snake):
            px = x * self.grid_size
            py = y * self.grid_size
            rect = pygame.Rect(px + 1, py + 1, self.grid_size - 2, self.grid_size - 2)

            if index == 0:
                pygame.draw.rect(self.screen, self.LIGHT_GREEN, rect)
                eye_l = pygame.Rect(px + 5, py + 5, 3, 3)
                eye_r = pygame.Rect(px + 12, py + 5, 3, 3)
                pygame.draw.rect(self.screen, self.BLACK, eye_l)
                pygame.draw.rect(self.screen, self.BLACK, eye_r)
            else:
                pygame.draw.rect(self.screen, self.NOKIA_GREEN, rect)

            pygame.draw.rect(self.screen, self.DARK_GREEN, rect, 1)

    def _draw_fruit(self):
        x, y = self.fruit
        px = x * self.grid_size
        py = y * self.grid_size

        glow = pygame.Rect(px - 2, py - 2, self.grid_size + 4, self.grid_size + 4)
        pygame.draw.rect(self.screen, self.ORANGE, glow, 2)

        fruit = pygame.Rect(px + 2, py + 2, self.grid_size - 4, self.grid_size - 4)
        pygame.draw.rect(self.screen, self.RED, fruit)

        shine = pygame.Rect(px + 4, py + 4, 4, 4)
        pygame.draw.rect(self.screen, self.WHITE, shine)

    def _draw_particles(self):
        for particle in self.particles:
            alpha = int(255 * (particle["life"] / particle["max_life"]))
            size = max(1, int(3 * (particle["life"] / particle["max_life"])))
            particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            color = (*self.ORANGE, alpha)
            pygame.draw.circle(particle_surface, color, (size, size), size)
            self.screen.blit(particle_surface, (int(particle["x"] - size), int(particle["y"] - size)))

    def _draw_hud(self):
        score_text = self.font.render(f"Score: {self.score}", True, self.WHITE)
        self.screen.blit(score_text, (14, 12))

        if self.speed_boost:
            boost_text = self.small_font.render("BOOST", True, self.LIGHT_GREEN)
            self.screen.blit(boost_text, (16, 48))

    def draw(self):
        if self.game_state == GameState.MAIN_MENU:
            self.ui_manager.draw_main_menu(self.screen)
            pygame.display.flip()
            return

        if self.game_state == GameState.SETTINGS:
            self.ui_manager.draw_settings_menu(self.screen)
            pygame.display.flip()
            return

        self.screen.fill(self.BLACK)
        self._draw_grid()
        self._draw_snake()
        self._draw_fruit()
        self._draw_particles()
        self._draw_hud()

        if self.game_state == GameState.GAME_OVER:
            self.ui_manager.draw_game_over_overlay(self.screen, self.score)

        pygame.display.flip()

    def quit(self):
        pygame.quit()
