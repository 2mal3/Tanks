import pygame as pg

import tanks.store as store


CREDITS_TEXT = [
    "[h1]Tanks",
    "A small tank game for school made with pygame",
    "",
    "[h2]Ideas",
    "LeoHerzog",
    "maariaan",
    "2mal3",
    "liam-hoyt",
    "",
    "[h2]Code",
    "2mal3",
    "LeoHerzog",
    "liam-hoyt",
    "maariaan",
    "",
    "[h2]Graphics",
    "maariaan",
    "liam-hoyt",
    "LeoHerzog",
    "",
    "[h2]Sound",
    "liam-hoyt",
    "maariaan",
    "",
    "[h2]Map Design",
    "liam-hoyt",
    "maarian",
    "",
    "[h2]Playtesting",
    "2mal3",
    "LeoHerzog",
    "liam-hoyt",
    "maariaan",
    "Jonas",
    "LuisSchuimer",
]


class TextLine:
    def __init__(self, screen: pg.Surface, image: pg.Surface, pos: tuple[float, float]):
        self.exact_y = pos[1]
        self.screen = screen
        self.image = image
        self.rect = pg.Rect(pos, self.image.get_size())

    def draw(self):
        self.screen.blit(self.image, self.rect)

    def update(self):
        self.exact_y -= 0.5
        self.rect.y = self.exact_y


class Credits:
    def __init__(self):
        self.clock = pg.time.Clock()
        self.SIZE = (800, 600)
        self.screen = pg.display.set_mode(self.SIZE)
        pg.display.set_caption("Credits")

        self.running = True

        self.text: list[TextLine] = []
        self.generate_text(CREDITS_TEXT)

        self.loop()

    def generate_text(self, text: list[str]):
        y = self.SIZE[1]

        for line in text:
            if line.startswith("[h1]"):
                font = store.BIG_FONT
                line = line.removeprefix("[h1]")
            elif line.startswith("[h2]"):
                font = store.NORMAL_FONT
                line = line.removeprefix("[h2]")
            else:
                font = store.SMALL_FONT

            text_img = store.generate_text(line, font=font)
            self.text.append(TextLine(
                self.screen,
                text_img,
                (self.SIZE[0]/2 - text_img.get_width()/2, y)
            ))

            y += font.get_sized_height()

    def loop(self):
        while self.running:
            pg.time.Clock().tick(store.FPS)

            # Update
            for text in self.text:
                text.update()

            if self.text[-1].rect.y < 0:
                self.running = False

            # Draw
            self.screen.fill(store.BLACK)
            for text in self.text:
                text.draw()

            pg.display.flip()

            # Quiting
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False


if __name__ == "__main__":
    Credits()
