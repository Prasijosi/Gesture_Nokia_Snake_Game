import os
import pygame

class UIManager:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        self.title_font = pygame.font.Font(None, 78)
        self.button_font = pygame.font.Font(None, 38)
        self.text_font = pygame.font.Font(None, 28)

        self.master_volume = 0.6
        self.sound_enabled = True
        self.selected_mode_label = "Classic"
        self.selected_skin_label = "Classic"

        self.COLORS = {
            "bg_top": (37, 62, 12),
            "bg_bottom": (110, 142, 20),
            "panel": (22, 36, 8),
            "panel_border": (176, 210, 62),
            "button": (140, 171, 22),
            "button_hover": (188, 220, 50),
            "button_text": (20, 30, 8),
            "title": (235, 245, 220),
            "text": (215, 235, 168),
            "danger": (184, 68, 52),
            "danger_hover": (220, 88, 64),
        }

        # New order: Start, Mode, Skin, Settings, Quit
        self.main_buttons = {
            "start": pygame.Rect(self.width // 2 - 120, 210, 240, 56),
            "mode": pygame.Rect(self.width // 2 - 120, 276, 240, 50),
            "skin": pygame.Rect(self.width // 2 - 120, 332, 240, 50),
            "settings": pygame.Rect(self.width // 2 - 120, 388, 240, 56),
            "quit": pygame.Rect(self.width // 2 - 120, 454, 240, 56),
        }

        self.settings_buttons = {
            "volume_down": pygame.Rect(self.width // 2 - 140, 292, 60, 50),
            "volume_up": pygame.Rect(self.width // 2 + 80, 292, 60, 50),
            "sound_toggle": pygame.Rect(self.width // 2 - 120, 372, 240, 56),
            "back": pygame.Rect(self.width // 2 - 120, 446, 240, 56),
        }

        self.game_over_buttons = {
            "restart": pygame.Rect(self.width // 2 - 120, 388, 240, 56),
            "main_menu": pygame.Rect(self.width // 2 - 120, 458, 240, 56),
        }

        self.button_click_sound = self._load_button_click()
        self._apply_button_volume()

    def _load_button_click(self):
        if pygame.mixer.get_init() is None:
            return None

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", "GameStart.mp3")
        if not os.path.exists(path):
            return None

        if os.path.getsize(path) < 44:
            return None

        try:
            return pygame.mixer.Sound(path)
        except pygame.error:
            return None

    def _apply_button_volume(self):
        if self.button_click_sound is None:
            return

        level = self.master_volume if self.sound_enabled else 0.0
        self.button_click_sound.set_volume(level)

    def set_master_volume(self, volume: float):
        self.master_volume = max(0.0, min(1.0, volume))
        self._apply_button_volume()

    def set_sound_enabled(self, enabled: bool):
        self.sound_enabled = bool(enabled)
        self._apply_button_volume()

    def set_main_menu_labels(self, mode_label: str, skin_label: str):
        self.selected_mode_label = mode_label
        self.selected_skin_label = skin_label

    def _play_click(self):
        if self.button_click_sound is not None and self.sound_enabled:
            self.button_click_sound.play()

    def _draw_background(self, surface):
        top = self.COLORS["bg_top"]
        bottom = self.COLORS["bg_bottom"]

        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = (
                int(top[0] * (1 - t) + bottom[0] * t),
                int(top[1] * (1 - t) + bottom[1] * t),
                int(top[2] * (1 - t) + bottom[2] * t),
            )
            pygame.draw.line(surface, color, (0, y), (self.width, y))

    def _draw_panel(self, surface, rect):
        pygame.draw.rect(surface, self.COLORS["panel"], rect, border_radius=14)
        pygame.draw.rect(surface, self.COLORS["panel_border"], rect, 2, border_radius=14)

    def _draw_button(self, surface, rect, label: str, is_hovered: bool, is_danger: bool = False):
        if is_danger:
            base_color = self.COLORS["danger_hover"] if is_hovered else self.COLORS["danger"]
        else:
            base_color = self.COLORS["button_hover"] if is_hovered else self.COLORS["button"]

        pygame.draw.rect(surface, base_color, rect, border_radius=10)
        pygame.draw.rect(surface, self.COLORS["panel_border"], rect, 2, border_radius=10)

        text = self.button_font.render(label, True, self.COLORS["button_text"])
        text_rect = text.get_rect(center=rect.center)
        surface.blit(text, text_rect)

    def draw_main_menu(self, surface):
        self._draw_background(surface)

        panel = pygame.Rect(self.width // 2 - 240, 66, 480, 520)
        self._draw_panel(surface, panel)

        title = self.title_font.render("Snake Game", True, self.COLORS["title"])
        title_rect = title.get_rect(center=(self.width // 2, 130))
        surface.blit(title, title_rect)

        subtitle = self.text_font.render("Gesture Control", True, self.COLORS["text"])
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, 168))
        surface.blit(subtitle, subtitle_rect)

        mouse_pos = pygame.mouse.get_pos()
        mode_text = f"Mode: {self.selected_mode_label}"
        skin_text = f"Skin: {self.selected_skin_label}"
        # Draw in new order: Start, Mode, Skin, Settings, Quit
        self._draw_button(surface, self.main_buttons["start"], "Start Game", self.main_buttons["start"].collidepoint(mouse_pos))
        self._draw_button(surface, self.main_buttons["mode"], mode_text, self.main_buttons["mode"].collidepoint(mouse_pos))
        self._draw_button(surface, self.main_buttons["skin"], skin_text, self.main_buttons["skin"].collidepoint(mouse_pos))
        self._draw_button(surface, self.main_buttons["settings"], "Settings", self.main_buttons["settings"].collidepoint(mouse_pos))
        self._draw_button(surface, self.main_buttons["quit"], "Quit", self.main_buttons["quit"].collidepoint(mouse_pos), is_danger=True)

    def handle_main_menu_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        if self.main_buttons["mode"].collidepoint(event.pos):
            self._play_click()
            return "cycle_mode"

        if self.main_buttons["skin"].collidepoint(event.pos):
            self._play_click()
            return "cycle_skin"

        for action, rect in self.main_buttons.items():
            if action in ("mode", "skin"):
                continue
            if rect.collidepoint(event.pos):
                self._play_click()
                return action

        return None

    def draw_settings_menu(self, surface):
        self._draw_background(surface)

        panel = pygame.Rect(self.width // 2 - 250, 90, 500, 470)
        self._draw_panel(surface, panel)

        title = self.title_font.render("Settings", True, self.COLORS["title"])
        title_rect = title.get_rect(center=(self.width // 2, 156))
        surface.blit(title, title_rect)

        info = self.text_font.render("Adjust sound and gameplay feedback", True, self.COLORS["text"])
        info_rect = info.get_rect(center=(self.width // 2, 198))
        surface.blit(info, info_rect)

        volume_label = self.button_font.render(f"Volume: {int(self.master_volume * 100)}%", True, self.COLORS["title"])
        volume_rect = volume_label.get_rect(center=(self.width // 2, 268))
        surface.blit(volume_label, volume_rect)

        slider = pygame.Rect(self.width // 2 - 70, 306, 140, 22)
        pygame.draw.rect(surface, (70, 98, 20), slider, border_radius=8)
        fill = pygame.Rect(slider.x, slider.y, int(slider.width * self.master_volume), slider.height)
        pygame.draw.rect(surface, self.COLORS["button_hover"], fill, border_radius=8)

        mouse_pos = pygame.mouse.get_pos()
        self._draw_button(surface, self.settings_buttons["volume_down"], "-", self.settings_buttons["volume_down"].collidepoint(mouse_pos))
        self._draw_button(surface, self.settings_buttons["volume_up"], "+", self.settings_buttons["volume_up"].collidepoint(mouse_pos))

        sound_label = "Sound: ON" if self.sound_enabled else "Sound: OFF"
        self._draw_button(
            surface,
            self.settings_buttons["sound_toggle"],
            sound_label,
            self.settings_buttons["sound_toggle"].collidepoint(mouse_pos),
        )

        self._draw_button(surface, self.settings_buttons["back"], "Back", self.settings_buttons["back"].collidepoint(mouse_pos))

    def handle_settings_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        if self.settings_buttons["volume_down"].collidepoint(event.pos):
            self.master_volume = max(0.0, self.master_volume - 0.1)
            self._play_click()
            self._apply_button_volume()
            return "volume_changed"

        if self.settings_buttons["volume_up"].collidepoint(event.pos):
            self.master_volume = min(1.0, self.master_volume + 0.1)
            self._play_click()
            self._apply_button_volume()
            return "volume_changed"

        if self.settings_buttons["sound_toggle"].collidepoint(event.pos):
            self.sound_enabled = not self.sound_enabled
            self._play_click()
            self._apply_button_volume()
            return "sound_toggled"

        if self.settings_buttons["back"].collidepoint(event.pos):
            self._play_click()
            return "back"

        return None

    def draw_game_over_overlay(self, surface, score: int, high_score: int, mode_label: str):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(self.width // 2 - 250, 150, 500, 390)
        self._draw_panel(surface, panel)

        title = self.title_font.render("Game Over", True, self.COLORS["title"])
        title_rect = title.get_rect(center=(self.width // 2, 206))
        surface.blit(title, title_rect)

        score_text = self.button_font.render(f"Score: {score}", True, self.COLORS["text"])
        score_rect = score_text.get_rect(center=(self.width // 2, 250))
        surface.blit(score_text, score_rect)

        high_score_text = self.text_font.render(f"High Score: {high_score}", True, self.COLORS["text"])
        high_score_rect = high_score_text.get_rect(center=(self.width // 2, 282))
        surface.blit(high_score_text, high_score_rect)

        mode_text = self.text_font.render(f"Mode: {mode_label}", True, self.COLORS["text"])
        mode_rect = mode_text.get_rect(center=(self.width // 2, 308))
        surface.blit(mode_text, mode_rect)

        mouse_pos = pygame.mouse.get_pos()
        self._draw_button(surface, self.game_over_buttons["restart"], "Restart", self.game_over_buttons["restart"].collidepoint(mouse_pos))
        self._draw_button(surface, self.game_over_buttons["main_menu"], "Main Menu", self.game_over_buttons["main_menu"].collidepoint(mouse_pos))

    def handle_game_over_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        if self.game_over_buttons["restart"].collidepoint(event.pos):
            self._play_click()
            return "restart"

        if self.game_over_buttons["main_menu"].collidepoint(event.pos):
            self._play_click()
            return "main_menu"

        return None
