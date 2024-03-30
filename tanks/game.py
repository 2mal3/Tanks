from functools import cache
from math import sin, cos, radians
from random import choice, randint

import pygame as pg

import tanks.store as store


def _limit(value: int | float, min_value: int, max_value: int):
    return max(min(value, max_value), min_value)


@cache
def _rotate_surface(surface: pg.Surface, angle: int):
    return pg.transform.rotate(surface, angle)


@cache
def _scale_surface(surface: pg.Surface, size: tuple[int, int]):
    return pg.transform.scale(surface, size)


@cache
def _scale_surface_by(surface: pg.Surface, factor: float):
    return pg.transform.scale_by(surface, factor)


@cache
def _rot_center(image, angle, pos: tuple[int, int]) -> tuple[pg.Surface, pg.Rect]:
    rotated_image = _rotate_surface(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(center=(pos[0], pos[1])).center)
    return rotated_image, new_rect


@cache
def _get_shadow(size: tuple[int, int], opacity: int) -> pg.Surface:
    shadow = pg.Surface(size, pg.SRCALPHA)
    shadow.fill((0, 0, 0, opacity))
    return shadow


def for_tiles(game_map: list[list[str]], draw_func: callable):
    for y, row in enumerate(game_map):
        for x, tile in enumerate(row):
            draw_func(tile, x, y)


def get_tanks_stats(tank_path: str) -> store.TankStats:
    return store.TankStats(**store.ASSETS[tank_path])


class Map:
    def __init__(self, map_path: str):
        self.SIZE = (1600, 800)
        self.surface = pg.Surface(self.SIZE)

        self.tank_spawns: list[tuple[int, int]] = []
        self.image = None
        self.tile_map: list[list[str]] = []

        self.load(store.ASSETS[map_path])
        self.draw()

    def get_map(self) -> pg.Surface:
        if not self.image:
            raise ValueError("Map not loaded")

        return self.image

    def load(self, text: str):
        rows = text.split("\n")
        self.tile_map = [row.split(" ") for row in rows]

    def draw(self):
        for_tiles(self.tile_map, self.draw_grass)
        for_tiles(self.tile_map, self.draw_shadow)
        for_tiles(self.tile_map, self.draw_wall)
        for_tiles(self.tile_map, self.draw_spawns)

        buffer = pg.image.tostring(self.surface, "RGB")
        self.image = pg.image.frombuffer(buffer, self.SIZE, "RGB")

    def draw_grass(self, tile: str, x: int, y: int):
        if tile == "e":
            scaled_img = _scale_surface(store.ASSETS["/images/tiles/grass.png"], (32, 32))
            rotated_img = _rotate_surface(scaled_img, choice([0, 90, 180, -90]))

            # Randomly rotate the image
            self.surface.blit(rotated_img, (x * 32, y * 32))

            # Make the image randomly darker
            shadow = _get_shadow((32, 32), randint(0, 16))
            self.surface.blit(shadow, (x * 32, y * 32))

            # Add some bushes
            number = randint(1, 100)
            if number <= 3:
                self.surface.blit(store.ASSETS["/images/tiles/bush3.png"], (x * 32, y * 32))

            if 4 <= number <= 6:
                self.surface.blit(store.ASSETS["/images/tiles/bush4.png"], (x * 32, y * 32))

    def draw_shadow(self, tile: str, x: int, y: int):
        if tile == "w":
            shadow = _get_shadow((32, 32), 128)
            self.surface.blit(shadow, (x * 32 + 5, y * 32 + 5))

    def draw_wall(self, tile: str, x: int, y: int):
        if tile == "w":
            scaled_img = _scale_surface(store.ASSETS["/images/tiles/wall.png"], (32, 32))
            # Randomly rotate the image
            rotated_img = _rotate_surface(scaled_img, choice([0, 90, 180, -90]))

            self.surface.blit(rotated_img, (x * 32, y * 32))
            # Make the image randomly darker
            shadow = _get_shadow((32, 32), randint(0, 64))
            self.surface.blit(shadow, (x * 32, y * 32))

    def draw_spawns(self, tile: str, x: int, y: int):
        if tile == "s":
            img = store.ASSETS["/images/tiles/lodestone_top.png"]
            scaled_img = _scale_surface(img, (32, 32))
            self.surface.blit(scaled_img, (x * 32, y * 32))


class Game:
    def __init__(
        self,
        map_type: str,
        tanks: list[dict[str, any]],
    ):
        self.SIZE = (1600, 800)
        self.running = True
        self.screen = pg.display.set_mode(self.SIZE)
        pg.display.set_caption("Tanks")
        self.clock = pg.time.Clock()
        self.end_animation_frame = 0

        self.map_img = None
        self.entities: list[Entity] = []

        self.map_handler = Map(map_type)
        self.map_img = self.map_handler.get_map()
        self.tank_spawns: list[tuple[int, int]] = []
        self.calculate_map()

        teams = ["red", "blue"]
        for i, tank in enumerate(tanks):
            self.entities.append(
                Tank(
                    self,
                    self.tank_spawns[i],
                    tank["type"],
                    tank["keys"],
                    teams[i % 2],
                    tank["color"],
                )
            )

        self.game_loop()

    def calculate_map(self):
        for_tiles(self.map_handler.tile_map, self.place_wall)
        for_tiles(self.map_handler.tile_map, self.get_spawns)

    def place_wall(self, tile: str, x: int, y: int):
        if tile == "w":
            self.entities.append(Entity(self, (x * 32, y * 32), "block", None, True, (32, 32)))

    def get_spawns(self, tile: str, x: int, y: int):
        if tile == "s":
            self.tank_spawns.append((x * 32, y * 32))

    def game_loop(self):
        while self.running:
            self.clock.tick(store.FPS)

            # Logic
            for entity in self.entities:
                entity.update()

            # Draw
            self.screen.fill(store.BLACK)

            self.screen.blit(self.map_img, (0, 0))

            for entity in self.entities:
                entity.draw()

            # End animation
            if self.end_animation_frame > 0:
                self.end_animation_frame += 1
            if self.end_animation_frame > 100:
                text = store.generate_text("Game Over", font=store.BIG_FONT)
                draw_pos = (
                    (self.SIZE[0] / 2) - text.get_width() / 2,
                    (self.SIZE[1] / 2) - text.get_height() / 2,
                )
                self.screen.blit(text, draw_pos)
            if self.end_animation_frame > 400:
                self.running = False

            # Quit
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False

            # Draw FPS
            fps = str(int(round(self.clock.get_fps(), 0)))
            text = store.generate_text(fps)
            self.screen.blit(text, (5, 5))

            pg.display.flip()

    def end(self):
        self.end_animation_frame += 1


class Entity:
    """Base class for all entities in the game. Don't do much"""

    def __init__(
        self,
        game: Game,
        pos: tuple[float, float],
        team: str,
        image: pg.Surface | None,
        collision: bool = True,
        size: tuple[int, int] = None,
    ):
        self.game = game
        self.team = team
        self.collision = collision
        self.image = image
        if image:
            self.box = pg.Rect((*pos[:2], min(image.get_size()), min(image.get_size())))
        if size:
            self.box = pg.Rect((*pos[:2], *size))

    def update(self):
        pass

    def draw(self):
        if self.image:
            self.game.screen.blit(self.image, self.box)


class Tank(Entity):
    def __init__(
        self,
        game: Game,
        pos: tuple[float, float],
        tank_type_path: str,
        keys: dict[str, int],
        team: str,
        color: int,
    ):

        # Load the tank type from a file
        self.stats = get_tanks_stats(tank_type_path)
        self.current_ammo = self.stats.max_shells
        self.reload_cooldown = self.stats.reload_speed
        self.stats.color = color

        self.image = pg.transform.scale_by(
            store.ASSETS[
                f"/images/proprietary/tank/Tanks_base/tank{self.stats.image_type}_color{self.stats.color}.png"
            ],
            self.stats.body_scale,
        )
        self.turret_image = pg.transform.scale_by(
            store.ASSETS[
                f"/images/proprietary/tank/Cannons_color{self.stats.color}/cannon{self.stats.image_type}_1.png"
            ],
            self.stats.turret_scale,
        )
        super().__init__(game, pos, team, self.image)

        self.velocity = [0, 0]
        self.draw_angle = 0
        self.last_shot = 0
        self.turret_angle = 0
        self.is_destroyed = False
        self.is_exploding = False
        self.animation_frame = 0
        self.shots = [store.ASSETS[f"/sounds/shot/{i}.wav"] for i in range(1)]

        self.keys = keys

        self.health = self.stats.health
        self.turret_angle_speed = self.stats.turret_speed

    def update(self):
        if self.is_exploding:
            self.animation_frame += 0.1
            if self.animation_frame > 8:
                self.is_exploding = False
        if self.is_destroyed:
            return

        # Shoot cooldown
        if self.current_ammo != self.stats.max_shells:
            self.reload_cooldown -= 1

            if self.reload_cooldown == 0:
                self.reload_cooldown = self.stats.reload_speed
                self.current_ammo += 1

        # Keyboard input
        keys = pg.key.get_pressed()

        # Turret Rotation
        if store.MANUAL_TURRET:
            if keys[self.keys["turret_left"]]:
                self.turret_angle += self.stats.turret_speed
            if keys[self.keys["turret_right"]]:
                self.turret_angle -= self.stats.turret_speed
        else:
            self.turret_angle += self.turret_angle_speed

        # Reduce velocity, aka drift
        if not (keys[self.keys["up"]] or keys[self.keys["down"]]):
            self.velocity[1] *= self.stats.drift
            self.velocity[1] = 0 if abs(self.velocity[1]) < 0.1 else self.velocity[1]
        if not (keys[self.keys["left"]] or keys[self.keys["right"]]):
            self.velocity[0] *= self.stats.drift
            self.velocity[0] = 0 if abs(self.velocity[0]) < 0.1 else self.velocity[0]

        # Movement
        if keys[self.keys["up"]]:
            self.velocity[1] = _limit(
                self.velocity[1] - self.stats.acceleration,
                -self.stats.max_speed,
                self.stats.max_speed,
            )
        if keys[self.keys["down"]]:
            self.velocity[1] = _limit(
                self.velocity[1] + self.stats.acceleration,
                -self.stats.max_speed,
                self.stats.max_speed,
            )
        if keys[self.keys["left"]]:
            self.velocity[0] = _limit(
                self.velocity[0] - self.stats.acceleration,
                -self.stats.max_speed,
                self.stats.max_speed,
            )
        if keys[self.keys["right"]]:
            self.velocity[0] = _limit(
                self.velocity[0] + self.stats.acceleration,
                -self.stats.max_speed,
                self.stats.max_speed,
            )

        # Actual movement
        any_key_pressed = False
        if not (
            keys[self.keys["up"]]
            or keys[self.keys["down"]]
            or keys[self.keys["left"]]
            or keys[self.keys["right"]]
        ):
            any_key_pressed = True
        self.box.y += self.velocity[1]
        if self.check_collision():
            self.box.y -= self.velocity[1]
            if store.BOUNCE:
                self.velocity[1] *= -1
            if any_key_pressed:
                self.velocity[1] = 0
        self.box.x += self.velocity[0]
        if self.check_collision():
            self.box.x -= self.velocity[0]
            if store.BOUNCE:
                self.velocity[0] *= -1
            if any_key_pressed:
                self.velocity[0] = 0

        if keys[self.keys["shoot"]]:
            if pg.time.get_ticks() - self.last_shot > self.stats.cooldown:
                self.last_shot = pg.time.get_ticks()
                self.shoot()

    def check_collision(self) -> bool:
        for entity in filter(lambda e: e.collision, self.game.entities):
            if entity != self and self.box.colliderect(entity.box):
                return True

        return False

    def shoot(self):
        if self.current_ammo == 0:
            return
        self.current_ammo -= 1
        self.reload_cooldown = self.stats.reload_speed * 1.5

        choice(self.shots).play()
        self.turret_angle_speed *= -1
        pos = (
            self.box.center[0] + sin(radians(self.turret_angle)) * 50,
            self.box.center[1] + cos(radians(self.turret_angle)) * 50,
        )
        self.game.entities.append(
            Bullet(
                self.game,
                pos,
                self.turret_angle,
                self.stats.bullet_speed,
                self.stats.bullet_damage,
                self.team,
            )
        )

    def draw(self):
        # diagonal directions
        if self.velocity[0] > 0 > self.velocity[1]:
            self.draw_angle = 135
        elif self.velocity[0] > 0 and self.velocity[1] > 0:
            self.draw_angle = 45
        elif self.velocity[0] < 0 < self.velocity[1]:
            self.draw_angle = -45
        elif self.velocity[0] < 0 and self.velocity[1] < 0:
            self.draw_angle = -135
        # normal directions
        elif self.velocity[1] < 0:
            self.draw_angle = 180
        elif self.velocity[1] > 0:
            self.draw_angle = 0
        elif self.velocity[0] < 0:
            self.draw_angle = -90
        elif self.velocity[0] > 0:
            self.draw_angle = 90

        tank_img, tank_img_pos = _rot_center(self.image, self.draw_angle, self.box.center)

        # Rotate the turret correctly
        # https://matthew-brett.github.io/teaching/rotation_2d.html
        turret_pos_vector = (
            self.stats.turret_offset[0] * self.stats.body_scale,
            self.stats.turret_offset[1] * self.stats.body_scale,
        )
        vector_angle = self.draw_angle * -1  # Invert the angle since 0, 0 is top left
        rotated_turret_offset_vector = (
            cos(radians(vector_angle)) * turret_pos_vector[0]
            - sin(radians(vector_angle)) * turret_pos_vector[1],
            sin(radians(vector_angle)) * turret_pos_vector[0]
            + cos(radians(vector_angle)) * turret_pos_vector[1],
        )
        turret_pos = (
            self.box.center[0] + rotated_turret_offset_vector[0],
            self.box.center[1] + rotated_turret_offset_vector[1],
        )
        turret_image, turret_image_pos = _rot_center(
            self.turret_image, self.turret_angle, turret_pos
        )

        # Draw the tank and turret
        self.game.screen.blit(tank_img, tank_img_pos)
        self.game.screen.blit(turret_image, turret_image_pos)

        if not self.is_destroyed:
            # Show health
            health_percent = (self.health * 100) / self.stats.health
            start = (self.box.bottomleft[0], self.box.bottomleft[1] + 20)
            end = (
                self.box.bottomleft[0] + health_percent / 2,
                self.box.bottomleft[1] + 20,
            )
            pg.draw.line(self.game.screen, store.RED, start, end, 5)

            # Show ammo. If above 10, show percentage
            if self.stats.max_shells > 10:
                ammo_draw_count = int(round((self.current_ammo * 10) / self.stats.max_shells, 0))
            else:
                ammo_draw_count = self.current_ammo

            for i in range(ammo_draw_count):
                x = self.box.bottomleft[0] + i * 5
                pg.draw.line(
                    self.game.screen,
                    store.GOLDENROD,
                    (x, self.box.bottomleft[1] + 30),
                    (x, self.box.bottomleft[1] + 42),
                    3,
                )
                pg.draw.line(
                    self.game.screen,
                    store.DARK_GOLDENROD,
                    (x, self.box.bottomleft[1] + 30),
                    (x, self.box.bottomleft[1] + 33),
                    3,
                )

        # Explosion animation
        if self.is_exploding:
            raw_explosion_img = _scale_surface_by(
                store.ASSETS[f"/images/proprietary/explosion/{int(self.animation_frame)}.png"], 2.5
            )
            explosion_img, explosion_img_pos = _rot_center(raw_explosion_img, 0, self.box.center)
            self.game.screen.blit(explosion_img, explosion_img_pos)

        # Debug
        if store.DEBUG:
            pg.draw.rect(self.game.screen, store.RED, self.box, 1)

            debug_stats: dict[str, any] = {
                "He": self.health,
                "An": self.draw_angle,
                "Ve": self.velocity,
                "Am": self.current_ammo,
            }
            draw_pos = self.box.y
            for description, stat in debug_stats.items():
                store.SMALL_FONT.render_to(
                    self.game.screen,
                    (self.box.x, draw_pos),
                    f"{description}: {stat}",
                    store.WHITE,
                )
                draw_pos += 20

    def damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.death()

    def death(self):
        self.is_exploding = True
        self.is_destroyed = True
        self.image = store.ASSETS[
            f"/images/proprietary/tank/Broken_assets/tank{self.stats.image_type}_color1_broken.png"
        ]
        self.turret_image = store.ASSETS[
            f"/images/proprietary/tank/Broken_assets/cannon{self.stats.image_type}_1_broken.png"
        ]
        self.game.end()


class Bullet(Entity):
    def __init__(
        self,
        game: Game,
        pos: tuple[float, float],
        angle: int,
        speed: int,
        damage: int,
        team: str,
    ):
        image = _scale_surface(store.ASSETS["/images/shell.png"], (20, 20))
        super().__init__(game, pos, team, image, collision=False, size=(20, 20))
        self.angle = angle
        self.animation_frame = 0
        self.is_exploding = False

        self.speed = speed
        self.damage = damage

    def update(self):
        if self.is_exploding:
            self.animation_frame += 0.5
            if self.animation_frame > 8:
                self.game.entities.remove(self)
                del self
            return

        for entity in filter(lambda e: e.collision and e.team != self.team, self.game.entities):
            if self.box.colliderect(entity.box):
                self.is_exploding = True
                if isinstance(entity, Tank) and entity.health > 0:
                    entity.damage(self.damage)
                return

        self.box.x += sin(radians(self.angle)) * self.speed
        self.box.y += cos(radians(self.angle)) * self.speed

    def draw(self):
        if self.is_exploding:
            self.image = store.ASSETS[f"/images/proprietary/explosion/{int(self.animation_frame)}.png"]
            self.game.screen.blit(self.image, (self.box.x - 48, self.box.y - 48))
            return

        image, rect = _rot_center(self.image, self.angle, self.box.center)
        self.game.screen.blit(image, rect)

        if store.DEBUG:
            pg.draw.rect(self.game.screen, store.RED, self.box, 1)


if __name__ == "__main__":
    g = Game(
        "/maps/gras1.txt",
        [
            {
                "type": "/types/speedy.json",
                "keys": {
                    "up": pg.K_w,
                    "down": pg.K_s,
                    "left": pg.K_a,
                    "right": pg.K_d,
                    "shoot": pg.K_SPACE,
                    "turret_right": pg.K_x,
                    "turret_left": pg.K_y,
                },
                "color": 1,
            },
            {
                "type": "/types/minigun.json",
                "keys": {
                    "up": pg.K_UP,
                    "down": pg.K_DOWN,
                    "left": pg.K_LEFT,
                    "right": pg.K_RIGHT,
                    "shoot": pg.K_RETURN,
                    "turret_right": pg.K_MINUS,
                    "turret_left": pg.K_PERIOD,
                },
                "color": 2,
            },
        ],
    )
