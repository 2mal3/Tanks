import json
import os
from dataclasses import dataclass

import pygame as pg
from pygame import freetype

PATH = os.path.dirname(os.path.abspath(__file__))

pg.init()
pg.font.init()
pg.mixer.init()


@dataclass()
class TankStats:
    health: int
    max_speed: int
    acceleration: float
    turret_speed: float
    cooldown: int
    bullet_speed: int
    bullet_damage: int
    image_type: int
    body_scale: float
    turret_offset: list[int]
    turret_scale: float
    drift: float
    reload_speed: int
    max_shells: int
    name: str
    color: int = 1


def _load_assets(path: str) -> dict[str, any]:
    """
    Load assets from the specified path and return them as a dictionary.

    Args:
        path (str): The path to the directory containing the assets.

    Returns:
        dict[str, any]: A dictionary containing the loaded assets, where the keys are the asset names and the values are the loaded assets.

    """
    new_assets = {}

    for root, dirs, files in os.walk(path):
        for file in files:
            name = f"{root}/{file}".removeprefix(path).replace("\\", "/")

            # Images
            if file.endswith(".png"):
                img = pg.image.load(os.path.join(root, file))
                new_assets[name] = img
            # Sounds
            elif file.endswith(".wav"):
                sound = pg.mixer.Sound(os.path.join(root, file))
                new_assets[name] = sound
            # Tank stats
            elif file.endswith(".json"):
                with open(os.path.join(root, file)) as f:
                    data = json.load(f)
                new_assets[name] = data
            # Maps
            elif file.endswith(".txt"):
                with open(os.path.join(root, file)) as f:
                    data = f.read()
                new_assets[name] = data

    return new_assets


ASSETS = _load_assets(f"{PATH}/assets")

BIG_FONT = pg.freetype.Font(f"{PATH}/assets/Roboto-Regular.ttf", 80)
NORMAL_FONT = pg.freetype.Font(f"{PATH}/assets/Roboto-Regular.ttf", 40)
SMALL_FONT = pg.freetype.Font(f"{PATH}/assets/Roboto-Regular.ttf", 20)

DEBUG = False
BOUNCE = False
MANUAL_TURRET = False
FPS = 60

BLACK = (24, 24, 27)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (218, 83, 76)
GOLDENROD = (218, 165, 32)
DARK_GOLDENROD = (184, 134, 11)


def generate_text(
    text: str,
    *,
    font: pg.freetype.Font = NORMAL_FONT,
) -> pg.Surface:
    """A function to generate a surface with the specified text with a drop shadow."""

    offset = font.size // 10
    text_size: pg.Rect = font.get_rect(text)
    screen = pg.Surface([c + offset for c in text_size.size])

    # Transparent background
    screen = screen.convert_alpha()
    screen.fill((0, 0, 0, 0))

    font.render_to(screen, (offset, offset), text, DARK_GRAY)
    font.render_to(screen, (0, 0), text, WHITE)

    return screen
