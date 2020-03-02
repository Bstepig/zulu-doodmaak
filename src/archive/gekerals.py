import os
from typing import List

import pygame
from pygame import Rect, Surface
import sys, json


class Level:

    def __init__(self, plan):
        self.plan: List[List[bool]] = plan


def load_level(filename) -> Level:
    fullname = os.path.join('levels', filename + '.json')
    f = open(fullname, encoding="utf-8")
    data = json.loads(f.read())
    plan = [[bool(j) for j in i] for i in data['plan']]
    return Level(plan)


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname)
    if color_key is not None:
        image = image.convert()
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


def terminate():
    pygame.quit()
    sys.exit()


class Sprite(pygame.sprite.Sprite):
    def __init__(self, image: Surface, *groups):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_rect()

    def update(self, delta, *args):
        pass


class Unit:
    pos = [20, 20]
    is_selected: bool = False
    speed = 500
    target = [20, 20]
    direction = [0, 0]
    hp = 100
    max_hp = 100

    sprite: Sprite
    rect: Rect

    def __init__(self, image: Surface, *groups):
        self.sprite = Sprite(image, groups)
        self.rect = self.sprite.rect

    def update(self, delta, *args):
        # self.x += 20 * delta / 1000

        # pos[0]
        self.pos = [self.pos[0] + self.direction[0] * delta * self.speed / 1000, self.pos[1] + self.direction[
            1] * delta * self.speed / 1000]
        if (self.target[0] - self.pos[0]) * self.direction[0] < 0:
            self.pos[0] = self.target[0]
            self.direction[0] = 0
        if (self.target[1] - self.pos[1]) * self.direction[1] < 0:
            self.pos[1] = self.target[1]
            self.direction[1] = 1
        self.rect.x = round(self.pos[0] - self.rect.w / 2)
        self.rect.y = round(self.pos[1] - self.rect.h / 2)

    def set_target(self, target):
        self.target = target
        x = self.target[0] - self.pos[0]
        y = self.target[1] - self.pos[1]
        a = (abs(x) + abs(y))
        self.direction = [x / a, y / a]

    # def draw(self):
    #     super().draw()
    #     if self.is_selected:
    #         pygame.draw.rect(screen)


class Selection(Rect):
    is_active: bool = False

    def __init__(self):
        super().__init__(0, 0, 0, 0)

    def __bool__(self):
        return self.is_active

    def start(self, coord):
        self.is_active = True
        self.x = coord[0]
        self.y = coord[1]

    def end(self):
        self.normalize()
        self.is_active = False

    def draw(self, screen, coord):
        if self.is_active:
            self.w = coord[0] - self.x
            self.h = coord[1] - self.y

            w = abs(coord[0] - self.x)
            h = abs(coord[1] - self.y)
            x = min(self.x, coord[0])
            y = min(self.y, coord[1])

            s = pygame.Surface((w, h))
            s.set_alpha(50)
            s.fill(COLORS['blue'])

            # screen.blit(s, (x, y))
            pygame.draw.rect(screen, (255, 255, 255), self, 2)


def draw_cursor(screen, coord):
    global resources
    coord = pygame.mouse.get_pos()
    x, y = resources['cursor'].get_size()
    x = coord[0] - x / 2
    y = coord[1] - y / 2
    screen.blit(resources['cursor'], (x, y))


resources = dict()
COLORS = {
    'sand': (238, 201, 129),
    'blue': (0, 207, 255)
}


def load_resources():
    resources['cursor'] = load_image('cursor3.png')
    resources['unit'] = load_image('unit.png')


def main(args):
    pygame.display.init()
    pygame.font.init()

    size = width, height = WIDTH, HEIGHT = 1600, 900
    size_min = width, height = WIDTH, HEIGHT = 400, 225
    # screen = pygame.display.set_mode(size_min)
    screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
    pygame.display.set_caption('Gekerals')

    load_resources()
    print(load_level('1').plan)
    pygame.display.set_icon(resources['unit'])

    clock = pygame.time.Clock()
    pygame.mouse.set_visible(False)

    selection = Selection()
    units_group = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()
    unit = Unit(resources['unit'], units_group, all_sprites)

    units = [unit]

    running = True
    while running:
        mouse_coord = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    selection.start(mouse_coord)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    selection.end()
                    if selection.w >= 15 or selection.h >= 15:
                        for sprite in units:
                            if selection.colliderect(sprite.rect):
                                sprite.is_selected = True
                            else:
                                sprite.is_selected = False
                    else:
                        for sprite in units:
                            if sprite.is_selected:
                                sprite.set_target(mouse_coord)
                elif event.button == 3:
                    selection.end()
                    for sprite in units:
                        sprite.is_selected = False

        screen.fill(COLORS['sand'])

        all_sprites.draw(screen)
        [i.update(clock.tick()) for i in units]

        selection.draw(screen, mouse_coord)
        draw_cursor(screen, mouse_coord)
        pygame.display.flip()

    terminate()


if __name__ == '__main__':
    main(sys.argv)
