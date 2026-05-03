import json
import math
import os
import random
import time
from enum import Enum
from typing import Optional, Tuple

import pygame

from ui_manager import UIManager


class GameState(Enum):
    MAIN_MENU = 1
    SETTINGS = 2
    PLAYING = 3
    GAME_OVER = 4


class GameMode(Enum):
    CLASSIC = "Classic"
    TIME_ATTACK = "Time Attack"
    OBSTACLE = "Obstacle"
    MAZE = "Maze"


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

        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 20)

        self.ui_manager = UIManager(self.width, self.height)

        self.mode_cycle = [
            GameMode.CLASSIC,
            GameMode.TIME_ATTACK,
            GameMode.OBSTACLE,
            GameMode.MAZE,
        ]
        self.current_mode_index = 0
        self.current_mode = self.mode_cycle[self.current_mode_index]

        self.skin_cycle = ["Classic", "Neon", "Ice"]
        self.current_skin_index = 0
        self.current_skin = self.skin_cycle[self.current_skin_index]
        self.snake_skins = {
            "Classic": {
                "head": (190, 220, 40),
                "body": (155, 188, 15),
                "border": (90, 120, 10),
                "eye": (20, 20, 20),
            },
            "Neon": {
                "head": (35, 255, 180),
                "body": (24, 180, 220),
                "border": (8, 110, 130),
                "eye": (255, 255, 255),
            },
            "Ice": {
                "head": (173, 227, 255),
                "body": (122, 198, 255),
                "border": (58, 124, 186),
                "eye": (20, 40, 70),
            },
        }

        self.base_speed = 8
        self.camera_boost_speed = 14
        self.camera_speed_boost = False

        self.food_catalog = [
            {"kind": "apple", "points": 10, "growth": 1, "color": (224, 62, 54)},
            {"kind": "banana", "points": 20, "growth": 2, "color": (240, 211, 73)},
            {"kind": "berry", "points": 30, "growth": 2, "color": (170, 90, 210)},
        ]
        self.max_food_items = 3

        self.power_up_catalog = [
            {"kind": "speed_boost", "label": "Speed", "duration": 7.0, "color": (255, 215, 70)},
            {"kind": "shield", "label": "Shield", "duration": 0.0, "color": (110, 190, 255)},
            {"kind": "slow_motion", "label": "Slow", "duration": 6.0, "color": (120, 240, 255)},
            {"kind": "shrink", "label": "Shrink", "duration": 0.0, "color": (255, 130, 180)},
        ]

        self.effect_timers = {"speed_boost": 0.0, "slow_motion": 0.0}
        self.power_up = None
        self.next_power_up_spawn_time = time.time() + random.uniform(9.0, 14.0)

        self.sound_enabled = True
        self.master_volume = 0.6
        self.eat_sound = self._load_sound(["eat_fruit.wav", "eatfruit.mp3"])
        self.game_over_sound = self._load_sound(["game_over.wav", "GameOver.mp3"])
        self.power_up_sound = self._load_sound(["button_click.wav", "GameStart.mp3"])
        self.apply_sound_volume()

        self.high_score_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "high_score.json")
        self.high_score = self._load_high_score()

        self.game_state = GameState.MAIN_MENU
        self.paused = False
        self.last_pause_toggle_time = 0.0

        self.camera_fps = 0.0
        self.gesture_indicator = "None"
        # Camera-driven free movement switch + last finger pos (normalised)
        self.camera_free_movement = False
        self.camera_finger_pos = None

        self.mode_start_time = time.time()
        self.logic_time = time.time()
        self.time_attack_duration = 60.0
        self.total_paused_time = 0.0
        self.pause_started_at = None

        self.obstacles = set()
        self.last_obstacle_spawn_time = time.time()

        self.particles = []
        self.reset_game()

    def _load_sound(self, filenames):
        if pygame.mixer.get_init() is None:
            return None

        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
        for filename in filenames:
            sound_path = os.path.join(base_dir, filename)
            if not os.path.exists(sound_path):
                continue
            if os.path.getsize(sound_path) < 44:
                continue
            try:
                return pygame.mixer.Sound(sound_path)
            except pygame.error:
                continue

        return None

    def apply_sound_volume(self):
        level = self.master_volume if self.sound_enabled else 0.0

        if self.eat_sound is not None:
            self.eat_sound.set_volume(level)
        if self.game_over_sound is not None:
            self.game_over_sound.set_volume(level)
        if self.power_up_sound is not None:
            self.power_up_sound.set_volume(level)

        self.ui_manager.set_master_volume(self.master_volume)
        self.ui_manager.set_sound_enabled(self.sound_enabled)

    def set_master_volume(self, volume: float):
        self.master_volume = max(0.0, min(1.0, volume))
        self.apply_sound_volume()

    def _load_high_score(self) -> int:
        if not os.path.exists(self.high_score_file):
            return 0

        try:
            with open(self.high_score_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                value = int(data.get("high_score", 0))
                return max(0, value)
        except (OSError, ValueError, json.JSONDecodeError):
            return 0

    def _save_high_score(self):
        try:
            with open(self.high_score_file, "w", encoding="utf-8") as file:
                json.dump({"high_score": self.high_score}, file)
        except OSError:
            pass

    def _update_high_score_if_needed(self):
        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()

    def cycle_mode(self):
        self.current_mode_index = (self.current_mode_index + 1) % len(self.mode_cycle)
        self.current_mode = self.mode_cycle[self.current_mode_index]

    def cycle_skin(self):
        self.current_skin_index = (self.current_skin_index + 1) % len(self.skin_cycle)
        self.current_skin = self.skin_cycle[self.current_skin_index]

    def _is_cell_blocked(self, cell):
        if cell in self.snake:
            return True
        if cell in self.obstacles:
            return True

        for food in self.food_items:
            if food["position"] == cell:
                return True

        if self.power_up is not None and self.power_up["position"] == cell:
            return True

        return False

    def _random_empty_cell(self):
        for _ in range(500):
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            cell = (x, y)
            if not self._is_cell_blocked(cell):
                return cell
        return None

    def _generate_maze_obstacles(self):
        obstacles = set()
        # Reserve a clear rectangle in the center for the snake spawn and first moves
        center_x = self.grid_width // 2
        center_y = self.grid_height // 2
        clear_radius_x = 3  # 3 cells left/right
        clear_radius_y = 2  # 2 cells up/down
        def is_in_spawn_area(x, y):
            return (
                center_x - clear_radius_x <= x <= center_x + clear_radius_x
                and center_y - clear_radius_y <= y <= center_y + clear_radius_y
            )

        for y in range(4, self.grid_height - 4):
            if y % 4 == 0:
                for x in range(3, self.grid_width - 3):
                    if is_in_spawn_area(x, y):
                        continue
                    obstacles.add((x, y))
        return obstacles

    def _seed_obstacles(self, count: int):
        for _ in range(count):
            cell = self._random_empty_cell()
            if cell is not None:
                self.obstacles.add(cell)

    def _spawn_food_item(self):
        cell = self._random_empty_cell()
        if cell is None:
            return None

        template = random.choice(self.food_catalog)
        return {
            "kind": template["kind"],
            "points": template["points"],
            "growth": template["growth"],
            "color": template["color"],
            "position": cell,
            "phase": random.uniform(0.0, math.pi * 2),
        }

    def _spawn_food_items(self):
        self.food_items = []
        for _ in range(self.max_food_items):
            item = self._spawn_food_item()
            if item is not None:
                self.food_items.append(item)

    def _spawn_power_up(self, now: float, force: bool = False):
        if self.power_up is not None:
            return

        if not force and now < self.next_power_up_spawn_time:
            return

        cell = self._random_empty_cell()
        if cell is None:
            self.next_power_up_spawn_time = now + random.uniform(8.0, 12.0)
            return

        template = random.choice(self.power_up_catalog)
        self.power_up = {
            "kind": template["kind"],
            "label": template["label"],
            "duration": template["duration"],
            "color": template["color"],
            "position": cell,
            "spawn_time": now,
            "phase": random.uniform(0.0, math.pi * 2),
        }

    def _consume_power_up(self, power_up):
        kind = power_up["kind"]
        if kind == "speed_boost":
            self.effect_timers["speed_boost"] = max(self.effect_timers["speed_boost"], power_up["duration"])
        elif kind == "shield":
            self.shield_charges = min(1, self.shield_charges + 1)
        elif kind == "slow_motion":
            self.effect_timers["slow_motion"] = max(self.effect_timers["slow_motion"], power_up["duration"])
        elif kind == "shrink":
            trim = min(4, max(0, len(self.snake) - 3))
            for _ in range(trim):
                self.snake.pop()

        if self.sound_enabled and self.power_up_sound is not None:
            self.power_up_sound.play()

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
        self.paused = False

        self.camera_speed_boost = False
        self.shield_charges = 0
        self.growth_pending = 0

        self.particles = []
        self.food_items = []
        self.obstacles = set()

        self.effect_timers = {"speed_boost": 0.0, "slow_motion": 0.0}

        self.mode_start_time = time.time()
        self.logic_time = self.mode_start_time
        self.total_paused_time = 0.0
        self.pause_started_at = None

        if self.current_mode == GameMode.MAZE:
            self.obstacles = self._generate_maze_obstacles()
        elif self.current_mode == GameMode.OBSTACLE:
            self._seed_obstacles(16)
            self.last_obstacle_spawn_time = self.mode_start_time

        self._spawn_food_items()
        self.power_up = None
        self.next_power_up_spawn_time = self.mode_start_time + random.uniform(8.0, 12.0)
        # pixel positions for free movement mode (centre of grid cells)
        self.snake_pixels = [
            (x * self.grid_size + self.grid_size // 2, y * self.grid_size + self.grid_size // 2)
            for x, y in self.snake
        ]

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
            elif action == "cycle_mode":
                self.cycle_mode()
            elif action == "cycle_skin":
                self.cycle_skin()

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
                    self.paused = False
                elif event.key == pygame.K_SPACE:
                    self.toggle_pause()
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
        if self.paused:
            return

        opposite = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }

        if new_direction != opposite[self.direction]:
            self.next_direction = new_direction

    def toggle_pause(self):
        if self.game_state == GameState.PLAYING:
            now = time.time()
            if not self.paused:
                self.paused = True
                self.pause_started_at = now
            else:
                self.paused = False
                if self.pause_started_at is not None:
                    self.total_paused_time += now - self.pause_started_at
                self.pause_started_at = None

    def handle_gesture(self, gesture: str):
        if self.game_state != GameState.PLAYING:
            return

        if gesture == "PAUSE":
            now = time.time()
            if now - self.last_pause_toggle_time > 0.7:
                self.toggle_pause()
                self.last_pause_toggle_time = now
            return

        if self.paused:
            return

        mapping = {
            "UP": Direction.UP,
            "DOWN": Direction.DOWN,
            "LEFT": Direction.LEFT,
            "RIGHT": Direction.RIGHT,
        }

        new_direction = mapping.get(gesture)
        if new_direction is not None:
            self._set_next_direction(new_direction)

    def set_runtime_stats(self, camera_fps: float, gesture: Optional[str], finger_pos: Optional[Tuple[float, float]] = None):
        """Called every frame from the manager with camera stats and optional finger position (normalised).
        """
        self.camera_fps = max(0.0, float(camera_fps))
        self.gesture_indicator = gesture if gesture else "None"
        self.camera_finger_pos = finger_pos

    def set_speed_boost(self, boost: bool):
        self.camera_speed_boost = bool(boost)


    def get_current_speed(self) -> int:
        speed = float(self.base_speed)

        if self.current_mode == GameMode.TIME_ATTACK:
            speed += 1.5

        if self.effect_timers["slow_motion"] > 0.0:
            speed -= 3.0

        if self.effect_timers["speed_boost"] > 0.0:
            speed += 4.0

        if self.camera_speed_boost:
            speed = max(speed, float(self.camera_boost_speed))

        return max(4, int(round(speed)))

    def add_particle_effect(self, x: int, y: int, color=(244, 154, 37)):
        for _ in range(12):
            self.particles.append(
                {
                    "x": x * self.grid_size + self.grid_size // 2,
                    "y": y * self.grid_size + self.grid_size // 2,
                    "vx": random.uniform(-2.8, 2.8),
                    "vy": random.uniform(-2.8, 2.8),
                    "life": 26,
                    "max_life": 26,
                    "color": color,
                }
            )

    def update_particles(self):
        for particle in self.particles[:]:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["life"] -= 1
            if particle["life"] <= 0:
                self.particles.remove(particle)

    def _set_game_over(self):
        self.game_over = True
        self.game_state = GameState.GAME_OVER
        self._update_high_score_if_needed()

        if not self.game_over_sound_played and self.sound_enabled and self.game_over_sound is not None:
            self.game_over_sound.play()
            self.game_over_sound_played = True

    def _handle_collision(self, cell):
        if self.shield_charges > 0:
            self.shield_charges -= 1
            self.add_particle_effect(cell[0], cell[1], color=(130, 220, 255))
            return False
        return True

    def _update_timers(self, dt: float):
        for key in self.effect_timers:
            self.effect_timers[key] = max(0.0, self.effect_timers[key] - dt)

        if self.current_mode == GameMode.TIME_ATTACK:
            remaining = self.time_attack_duration - self._get_mode_elapsed_seconds()
            if remaining <= 0:
                self._set_game_over()

    def _get_mode_elapsed_seconds(self):
        elapsed = time.time() - self.mode_start_time - self.total_paused_time
        if self.paused and self.pause_started_at is not None:
            elapsed -= max(0.0, time.time() - self.pause_started_at)
        return max(0.0, elapsed)

    def _update_obstacle_mode(self, now: float):
        if self.current_mode != GameMode.OBSTACLE:
            return

        if now - self.last_obstacle_spawn_time < 6.0:
            return

        self.last_obstacle_spawn_time = now
        if len(self.obstacles) >= 70:
            return

        cell = self._random_empty_cell()
        if cell is not None:
            self.obstacles.add(cell)

    def update(self):
        now = time.time()
        dt = max(0.0, now - self.logic_time)
        self.logic_time = now

        self.update_particles()

        if self.game_state != GameState.PLAYING or self.game_over:
            return

        if self.paused:
            return

        self._update_timers(dt)
        if self.game_over:
            return

        self._update_obstacle_mode(now)
        self._spawn_power_up(now)

        if self.paused:
            return

        # Camera-driven free movement (pixel-based)
        if self.camera_free_movement and self.camera_finger_pos is not None and hasattr(self, "snake_pixels") and len(self.snake_pixels) > 0:
            # head pixel position
            head_px_x, head_px_y = self.snake_pixels[0]

            target_x = max(0.0, min(1.0, self.camera_finger_pos[0])) * self.width
            target_y = max(0.0, min(1.0, self.camera_finger_pos[1])) * self.height

            vx = target_x - head_px_x
            vy = target_y - head_px_y
            dist = math.hypot(vx, vy)

            if dist > 1e-3:
                nx = vx / dist
                ny = vy / dist
                pixels_per_step = self.grid_size * (self.get_current_speed() / 8.0)
                move_x = nx * pixels_per_step
                move_y = ny * pixels_per_step
            else:
                move_x = move_y = 0.0

            new_head_px = (head_px_x + move_x, head_px_y + move_y)

            # Convert to grid cell for collisions and game logic
            new_head_cell = (int(new_head_px[0] // self.grid_size), int(new_head_px[1] // self.grid_size))

            wall_hit = (
                new_head_cell[0] < 0
                or new_head_cell[0] >= self.grid_width
                or new_head_cell[1] < 0
                or new_head_cell[1] >= self.grid_height
            )
            body_hit = new_head_cell in self.snake
            obstacle_hit = new_head_cell in self.obstacles

            if wall_hit or body_hit or obstacle_hit:
                if self._handle_collision(new_head_cell):
                    self._set_game_over()
                return

            # insert new head at pixel and logical cell lists
            self.snake_pixels.insert(0, new_head_px)
            self.snake.insert(0, new_head_cell)

            consumed_food = None
            for food in self.food_items:
                if food["position"] == new_head_cell:
                    consumed_food = food
                    break
        else:
            # Grid-based movement (original behaviour)
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
            obstacle_hit = new_head in self.obstacles

            if wall_hit or body_hit or obstacle_hit:
                if self._handle_collision(new_head):
                    self._set_game_over()
                return

            self.snake.insert(0, new_head)
            # also keep snake_pixels in sync for drawing
            if hasattr(self, "snake_pixels"):
                new_head_px = (new_head[0] * self.grid_size + self.grid_size // 2,
                               new_head[1] * self.grid_size + self.grid_size // 2)
                self.snake_pixels.insert(0, new_head_px)

            consumed_food = None
            for food in self.food_items:
                if food["position"] == new_head:
                    consumed_food = food
                    break

        if consumed_food is not None:
            self.score += consumed_food["points"]
            self._update_high_score_if_needed()
            self.growth_pending += consumed_food["growth"]
            head_cell = self.snake[0]
            self.add_particle_effect(head_cell[0], head_cell[1], color=consumed_food["color"])
            self.food_items.remove(consumed_food)

            replacement = self._spawn_food_item()
            if replacement is not None:
                self.food_items.append(replacement)

            if self.sound_enabled and self.eat_sound is not None:
                self.eat_sound.play()

            if random.random() < 0.18:
                self._spawn_power_up(now, force=True)

        if self.power_up is not None and self.power_up["position"] == self.snake[0]:
            self._consume_power_up(self.power_up)
            head_cell = self.snake[0]
            self.add_particle_effect(head_cell[0], head_cell[1], color=self.power_up["color"])
            self.power_up = None
            self.next_power_up_spawn_time = now + random.uniform(8.0, 12.0)

        if self.growth_pending > 0:
            self.growth_pending -= 1
        else:
            # always keep both lists in sync
            if hasattr(self, "snake_pixels") and len(self.snake_pixels) > 0:
                self.snake_pixels.pop()
            if len(self.snake) > 0:
                self.snake.pop()

    def _draw_misty_background(self):
        # Soft vertical gradient
        top = (200, 210, 220)
        bottom = (160, 170, 180)
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = (
                int(top[0] * (1 - t) + bottom[0] * t),
                int(top[1] * (1 - t) + bottom[1] * t),
                int(top[2] * (1 - t) + bottom[2] * t),
            )
            pygame.draw.line(self.screen, color, (0, y), (self.width, y))

        # Mist/fog overlays
        mist = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for i in range(3):
            alpha = 28 + i * 10
            pygame.draw.ellipse(
                mist,
                (220, 225, 230, alpha),
                pygame.Rect(-120 + i * 80, 60 + i * 90, self.width + 180, 180 + i * 40),
            )
        self.screen.blit(mist, (0, 0))

    def _draw_obstacles(self):
        # Render obstacles as organic stones/bamboo
        for x, y in self.obstacles:
            px = x * self.grid_size + self.grid_size // 2
            py = y * self.grid_size + self.grid_size // 2
            stone_color = (170, 175, 180)
            edge_color = (120, 130, 140)
            # Slight random size/shape for organic look
            radius = self.grid_size // 2 - 2 + random.randint(-2, 2)
            offset_x = random.randint(-2, 2)
            offset_y = random.randint(-2, 2)
            pygame.draw.ellipse(
                self.screen,
                stone_color,
                pygame.Rect(px - radius + offset_x, py - radius + offset_y, radius * 2, radius * 2),
            )
            pygame.draw.ellipse(
                self.screen,
                edge_color,
                pygame.Rect(px - radius + offset_x, py - radius + offset_y, radius * 2, radius * 2),
                2,
            )

    def _draw_snake(self):
        skin = self.snake_skins[self.current_skin]
        head_color = skin["head"]
        body_color = skin["body"]
        border_color = skin["border"]
        eye_color = skin["eye"]

        # use snake_pixels if in camera free movement and lists are synced, otherwise compute from grid
        if self.camera_free_movement and hasattr(self, "snake_pixels") and len(self.snake_pixels) == len(self.snake) and len(self.snake_pixels) > 0:
            iter_seq = list(self.snake_pixels)
        elif hasattr(self, "snake_pixels") and len(self.snake_pixels) == len(self.snake) and len(self.snake_pixels) > 0:
            iter_seq = list(self.snake_pixels)
        else:
            # fallback: compute from grid cells
            iter_seq = [
                (x * self.grid_size + self.grid_size // 2, y * self.grid_size + self.grid_size // 2)
                for (x, y) in self.snake
            ]

        for index, (px, py) in enumerate(iter_seq):

            scale = 1.0
            if self.growth_pending > 0 and index == 0:
                scale = 1.08

            radius = int((self.grid_size // 2 - 2) * scale)
            color = head_color if index == 0 else body_color
            # Soft shadow
            pygame.draw.circle(self.screen, (180, 185, 190), (int(px), int(py + 3)), radius + 2)
            pygame.draw.circle(self.screen, color, (int(px), int(py)), radius)
            pygame.draw.circle(self.screen, border_color, (int(px), int(py)), radius, 2)

            if index == 0:
                # Eyes
                eye_offset = radius // 2
                pygame.draw.circle(self.screen, eye_color, (int(px - eye_offset // 2), int(py - eye_offset // 2)), 3)
                pygame.draw.circle(self.screen, eye_color, (int(px + eye_offset // 2), int(py - eye_offset // 2)), 3)

    def _draw_food_items(self):
        now = time.time()
        for food in self.food_items:
            x, y = food["position"]
            px = x * self.grid_size + self.grid_size // 2
            py = y * self.grid_size + self.grid_size // 2

            pulse = 1.0 + 0.15 * math.sin(now * 6.0 + food["phase"])
            radius = max(5, int((self.grid_size // 2 - 2) * pulse))

            if food["kind"] == "apple":
                # Apple: soft red with a highlight
                pygame.draw.circle(self.screen, food["color"], (px, py), radius)
                pygame.draw.circle(self.screen, (255, 255, 255), (px - 3, py - 3), 3)
                pygame.draw.rect(self.screen, (120, 90, 40), pygame.Rect(px - 1, py - radius - 2, 2, 5))
            elif food["kind"] == "banana":
                # Banana: gentle arc
                banana_rect = pygame.Rect(px - radius, py - radius // 2, radius * 2, radius)
                pygame.draw.arc(self.screen, food["color"], banana_rect, 0.2, 2.8, 4)
                pygame.draw.arc(self.screen, (255, 255, 255), banana_rect, 0.5, 1.2, 2)
            else:
                # Berry: cluster of circles
                pygame.draw.circle(self.screen, food["color"], (px - 3, py), max(3, radius - 3))
                pygame.draw.circle(self.screen, food["color"], (px + 3, py), max(3, radius - 3))
                pygame.draw.circle(self.screen, food["color"], (px, py - 4), max(3, radius - 3))
                pygame.draw.circle(self.screen, (255, 255, 255), (px, py - 4), 1)

    def _draw_power_up(self):
        if self.power_up is None:
            return

        x, y = self.power_up["position"]
        px = x * self.grid_size + self.grid_size // 2
        py = y * self.grid_size + self.grid_size // 2
        color = self.power_up["color"]

        glow_surface = pygame.Surface((self.grid_size * 3, self.grid_size * 3), pygame.SRCALPHA)
        glow_alpha = int(90 + 45 * math.sin(time.time() * 8.0 + self.power_up["phase"]))
        pygame.draw.circle(
            glow_surface,
            (color[0], color[1], color[2], max(30, glow_alpha)),
            (glow_surface.get_width() // 2, glow_surface.get_height() // 2),
            self.grid_size,
        )
        self.screen.blit(glow_surface, (px - glow_surface.get_width() // 2, py - glow_surface.get_height() // 2))

        points = [
            (px, py - 8),
            (px + 8, py),
            (px, py + 8),
            (px - 8, py),
        ]
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, self.WHITE, points, 1)

    def _draw_particles(self):
        for particle in self.particles:
            alpha = int(255 * (particle["life"] / particle["max_life"]))
            size = max(1, int(3 * (particle["life"] / particle["max_life"])))
            particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            c = particle["color"]
            color = (c[0], c[1], c[2], alpha)
            pygame.draw.circle(particle_surface, color, (size, size), size)
            self.screen.blit(particle_surface, (int(particle["x"] - size), int(particle["y"] - size)))

    def _format_timer_text(self):
        if self.current_mode == GameMode.TIME_ATTACK:
            remaining = max(0.0, self.time_attack_duration - self._get_mode_elapsed_seconds())
            return f"Timer: {remaining:04.1f}s"

        elapsed = self._get_mode_elapsed_seconds()
        return f"Timer: {elapsed:04.1f}s"

    def _active_effect_text(self):
        labels = []
        if self.effect_timers["speed_boost"] > 0.0:
            labels.append(f"Speed+ {self.effect_timers['speed_boost']:0.1f}s")
        if self.effect_timers["slow_motion"] > 0.0:
            labels.append(f"Slow {self.effect_timers['slow_motion']:0.1f}s")
        if self.shield_charges > 0:
            labels.append("Shield x1")
        return " | ".join(labels) if labels else "None"

    def _draw_hud(self):
        score_text = self.font.render(f"Score: {self.score}", True, self.WHITE)
        high_text = self.small_font.render(f"High: {self.high_score}", True, self.WHITE)
        mode_text = self.small_font.render(f"Mode: {self.current_mode.value}", True, self.WHITE)
        timer_text = self.small_font.render(self._format_timer_text(), True, self.WHITE)

        self.screen.blit(score_text, (12, 10))
        self.screen.blit(high_text, (12, 42))
        self.screen.blit(mode_text, (12, 64))
        self.screen.blit(timer_text, (12, 86))

        fps_text = self.small_font.render(f"Cam FPS: {self.camera_fps:0.1f}", True, self.WHITE)
        gesture_text = self.small_font.render(f"Gesture: {self.gesture_indicator}", True, self.WHITE)
        speed_text = self.small_font.render(f"Speed: {self.get_current_speed()}", True, self.WHITE)

        self.screen.blit(fps_text, (self.width - 165, 10))
        self.screen.blit(gesture_text, (self.width - 210, 34))
        self.screen.blit(speed_text, (self.width - 145, 58))

        effect_text = self.tiny_font.render(f"Effects: {self._active_effect_text()}", True, self.WHITE)
        self.screen.blit(effect_text, (12, self.height - 22))

        if self.paused:
            paused = self.font.render("PAUSED", True, self.WHITE)
            paused_rect = paused.get_rect(center=(self.width // 2, 40))
            self.screen.blit(paused, paused_rect)

    def draw(self):
        if self.game_state == GameState.MAIN_MENU:
            self.ui_manager.set_main_menu_labels(self.current_mode.value, self.current_skin)
            self.ui_manager.draw_main_menu(self.screen)
            pygame.display.flip()
            return

        if self.game_state == GameState.SETTINGS:
            self.ui_manager.draw_settings_menu(self.screen)
            pygame.display.flip()
            return

        self._draw_misty_background()
        self._draw_obstacles()
        self._draw_food_items()
        self._draw_power_up()
        self._draw_snake()
        self._draw_particles()
        self._draw_hud()

        if self.game_state == GameState.GAME_OVER:
            self.ui_manager.draw_game_over_overlay(self.screen, self.score, self.high_score, self.current_mode.value)

        pygame.display.flip()

    def quit(self):
        pygame.quit()
