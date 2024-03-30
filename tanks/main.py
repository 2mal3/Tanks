from random import randint
from typing import Callable

import pygame as pg
from PIL import ImageFilter, Image

import tanks.store as store
from tanks.credits import Credits
from tanks.game import Game, get_tanks_stats, _rot_center, Map


class TextButton:
    def __init__(
        self, text: str, on_click: Callable, pos: tuple[int, int], *, font=store.NORMAL_FONT
    ):
        self.on_click = on_click
        self.text = store.generate_text(text, font=font)
        self.box = pg.Rect(pos, self.text.get_size())

    def try_handle_click(self, pos: tuple[int, int]):
        if self.box.collidepoint(pos):
            self.on_click()

    def draw(self, screen: pg.Surface):
        screen.blit(self.text, self.box.topleft)


class Button:
    def __init__(self, image: pg.Surface, on_click: Callable, pos: tuple[float, float]):
        self.image = image
        self.on_click = on_click
        self.bounds = self.image.get_rect(topleft=pos)

    def draw(self, screen):
        screen.blit(self.image, self.bounds.topleft)
        pg.draw.rect(screen, store.BLACK, self.bounds, 2)

    def try_handle_click(self, coordinate: tuple[int, int]):
        if self.bounds.collidepoint(coordinate):
            self.on_click()


class Window:
    def __init__(self):
        self.SIZE = (1040, 520)
        self.FONT_SIZE = 30

        # Main window
        self.screen = pg.display.set_mode(self.SIZE)
        pg.display.set_caption("Map Selection")

        # Tank attributes
        self.tank1image = None
        self.tank_1_index = 0
        self.tank_1_color = 1
        self.tank_2_index = 1
        self.tank_2_color = 2
        self.tank_paths = [name for name in store.ASSETS if "types" in name]
        self.gui_tank_stats = [self.get_tank_stats_from_index(self.tank_1_index), self.get_tank_stats_from_index(self.tank_2_index)]
        self.stats = ["Name: ", "Health: ", "Speed: ", "Damage: ", "Ammo: "]
        self.tank_stats_list = []

        # Map attributes
        self.map_index = 0
        self.map_paths = [file_name for file_name in store.ASSETS if "maps" in file_name]
        self.map_image = None
        self.set_map_image()

        # Buttons
        self.buttons: list[Button | TextButton] = []
        self.BUTTON_HEIGHT = (self.SIZE[1] // 3) + 4
        self.BUTTON_WIDTH = self.SIZE[0] // 10
        self.add_buttons()

        self.loop()

    def get_display_tank_stats(self, tank: str) -> list[str]:
        stats = get_tanks_stats(tank)
        name = str(stats.name)
        health = str(stats.health)
        speed = str(stats.max_speed)
        damage = str(stats.bullet_damage)
        ammo = str(stats.max_shells)

        return [name, health, speed, damage, ammo]

    def show_credits(self):
        Credits()
        self.after_subscreen_closed()

    def get_tank_stats_from_index(self, i: int) -> list[str]:
        tank_path = self.tank_paths[i]
        tank_stats = self.get_display_tank_stats(tank_path)
        return tank_stats

    def add_buttons(self):
        arrow_right = pg.transform.scale_by(store.ASSETS["/images/gui/pfeile-rechts.png"], 0.25)
        arrow_left = pg.transform.scale_by(store.ASSETS["/images/gui/pfeile-links.png"], 0.25)

        # Credits
        self.buttons.append(
            TextButton(
                "Credits",
                self.show_credits,
                (20, self.SIZE[1] - 35),
                font=store.SMALL_FONT,
            )
        )

        # Game start
        def on_click_start():
            self.start_game()

        self.buttons.append(
            Button(
                pg.transform.scale_by(store.ASSETS["/images/gui/start-button.png"], 0.1),
                on_click_start,
                (self.BUTTON_WIDTH * 4.35, self.BUTTON_HEIGHT)
            )
        )

        # Tank selection
        def on_click_player_1_left():
            self.tank_1_index += 1
            if self.tank_1_index >= len(self.tank_paths):
                self.tank_1_index = 0
            self.gui_tank_stats[0] = self.get_tank_stats_from_index(self.tank_1_index)
            self.tank_1_color = self.get_random_tank_color()

        self.buttons.append(
            Button(
                arrow_left,
                on_click_player_1_left,
                (self.BUTTON_WIDTH, self.BUTTON_HEIGHT + 85)
            )
        )

        def on_click_player_1_right():
            self.tank_1_index -= 1
            if self.tank_1_index < 0:
                self.tank_1_index = len(self.tank_paths) - 1
            self.gui_tank_stats[0] = self.get_tank_stats_from_index(self.tank_1_index)
            self.tank_1_color = self.get_random_tank_color()

        self.buttons.append(
            Button(
                arrow_right,
                on_click_player_1_right,
                (self.BUTTON_WIDTH * 2, self.BUTTON_HEIGHT + 85)
            )
        )

        def on_click_player_2_left():
            self.tank_2_index -= 1
            if self.tank_2_index < 0:
                self.tank_2_index = len(self.tank_paths) - 1
            self.gui_tank_stats[1] = self.get_tank_stats_from_index(self.tank_2_index)
            self.tank_2_color = self.get_random_tank_color()

        self.buttons.append(
            Button(
                arrow_left,
                on_click_player_2_left,
                (self.BUTTON_WIDTH * 7.5, self.BUTTON_HEIGHT + 85)
            )
        )

        def on_click_player_2_right():
            self.tank_2_index += 1
            if self.tank_2_index >= len(self.tank_paths):
                self.tank_2_index = 0
            self.gui_tank_stats[1] = self.get_tank_stats_from_index(self.tank_2_index)
            self.tank_2_color = self.get_random_tank_color()

        self.buttons.append(
            Button(
                arrow_right,
                on_click_player_2_right,
                (self.BUTTON_WIDTH * 8.5, self.BUTTON_HEIGHT + 85)
            )
        )

        # Map selection
        def on_click_map_left():
            self.map_index -= 1
            if self.map_index <= -1:
                self.map_index = len(self.map_paths) - 1
            self.set_map_image()

        self.buttons.append(
            Button(
                arrow_left,
                on_click_map_left,
                (self.BUTTON_WIDTH * 4.25, self.BUTTON_HEIGHT + 205)
            )
        )

        def on_click_map_right():
            self.map_index += 1
            if self.map_index >= len(self.map_paths):
                self.map_index = 0
            self.set_map_image()
            print(self.map_index)

        self.buttons.append(
            Button(
                arrow_right,
                on_click_map_right,
                (self.BUTTON_WIDTH * 5.25, self.BUTTON_HEIGHT + 205)
            )
        )

    def draw_text(self, text: str | list[str], position: tuple[float, float]):
        """
        Draws text on the screen.
        If text is a list, it will draw a line for each element of the list.
        If text is a string, it will draw it centered at the position.
        """

        font = pg.font.Font(None, self.FONT_SIZE)

        if type(text) is list:
            line_height = 20
            for line in text:
                text_rendered = font.render(line, True, store.RED)
                text_rect = text_rendered.get_rect(topleft=position)
                self.screen.blit(text_rendered, text_rect)
                position = [position[0], position[1] + line_height]

        elif type(text) is str:
            text_rendered = font.render(text, True, store.RED)
            text_rect = text_rendered.get_rect(center=position)
            self.screen.blit(text_rendered, text_rect)

    def draw_button(self, content: pg.Surface, rect: pg.Rect):
        self.screen.blit(content, rect)
        pg.draw.rect(self.screen, store.GRAY, rect, 1, 3)

    def get_random_tank_color(self) -> int:
        return randint(1, 5)

    def start_game(self):
        Game(
            self.map_paths[self.map_index],
            [
                {
                    "type": self.tank_paths[self.tank_1_index],
                    "keys": {
                        "up": pg.K_w,
                        "down": pg.K_s,
                        "left": pg.K_a,
                        "right": pg.K_d,
                        "shoot": pg.K_SPACE,
                    },
                    "color": self.tank_1_color,
                },
                {
                    "type": self.tank_paths[self.tank_2_index],
                    "keys": {
                        "up": pg.K_UP,
                        "down": pg.K_DOWN,
                        "left": pg.K_LEFT,
                        "right": pg.K_RIGHT,
                        "shoot": pg.K_RETURN,
                    },
                    "color": self.tank_2_color,
                },
            ],
        )
        self.after_subscreen_closed()

    def after_subscreen_closed(self):
        self.screen = pg.display.set_mode(self.SIZE)

    def loop(self):
        running = True
        while running:
            pg.time.Clock().tick(store.FPS)

            # Draw Map
            self.screen.blit(self.map_image, (0, 0))

            # Draw Tanks
            self.draw_tank((140, 100), self.tank_1_index, self.tank_1_color)
            self.draw_tank((815, 100), self.tank_2_index, self.tank_2_color)

            # Event handling
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    mouse_pos = pg.mouse.get_pos()

                    for button in self.buttons:
                        button.try_handle_click(mouse_pos)

            # Draw text
            self.draw_text("Welcome to the Game!", (self.SIZE[0] // 2, self.SIZE[1] // 5))

            # Draw Stats
            # Player 1
            self.draw_text(self.stats, (self.BUTTON_WIDTH * 1, self.BUTTON_HEIGHT + 115))
            self.draw_text(self.gui_tank_stats[0], (self.BUTTON_WIDTH * 2.5, self.BUTTON_HEIGHT + 115))
            # Player 2
            self.draw_text(self.stats, (self.BUTTON_WIDTH * 7.5, self.BUTTON_HEIGHT + 115))
            self.draw_text(self.gui_tank_stats[1], (self.BUTTON_WIDTH * 8.5, self.BUTTON_HEIGHT + 115))

            # Draw Buttons
            for button in self.buttons:
                button.draw(self.screen)

            pg.display.flip()

        pg.quit()

    def set_map_image(self):
        map_object = Map(self.map_paths[self.map_index])
        image = map_object.get_map()
        scaled_image = pg.transform.smoothscale(image, self.SIZE)

        # Blur the image
        pil_image = Image.frombytes(
            "RGB",
            (scaled_image.get_width(), scaled_image.get_height()),
            pg.image.tostring(scaled_image, "RGB"),
        )
        blurred_pil_image = pil_image.filter(ImageFilter.GaussianBlur())
        blurred_image = pg.image.frombuffer(
            blurred_pil_image.tobytes(), blurred_pil_image.size, "RGB"
        )

        self.map_image = blurred_image

    def draw_tank(self, pos: tuple[int, int], tank_type_number: int, color: int):
        tank_stats = get_tanks_stats(self.tank_paths[tank_type_number])
        turret_offset = tank_stats.turret_offset

        tank_image: pg.Surface = store.ASSETS[
            f"/images/proprietary/tank/Tanks_base/tank{tank_stats.image_type}_color{color}.png"
        ]
        turret_image: pg.Surface = store.ASSETS[
            f"/images/proprietary/tank/Cannons_color{color}/cannon{tank_stats.image_type}_1.png"
        ]

        turret_draw_center = (
            pos[0] + turret_offset[0] + tank_image.get_width() / 2,
            pos[1] + turret_offset[1] + tank_image.get_height() / 2,
        )
        _, turret_pos = _rot_center(turret_image, 1, turret_draw_center)

        self.screen.blit(tank_image, pos)
        self.screen.blit(turret_image, turret_pos)


if __name__ == "__main__":
    g = Window()
