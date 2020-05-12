import os
from typing import List, Dict

import pygame
import simpleaudio
from pygame import Surface

ANIMATION_TAGS = {
    'loop': 1
}


class Rect(pygame.Rect):

    def get_distance(self, rect: 'Rect'):
        if self.left <= rect.left <= self.right or self.left <= rect.right <= self.right:
            x = 0
        else:
            x = min(
                abs(rect.left - self.left), abs(rect.left - self.right),
                abs(rect.right - self.left), abs(rect.right - self.right),
            )
        if self.top <= rect.top <= self.bottom or self.top <= rect.bottom <= self.bottom:
            y = 0
        else:
            y = min(
                abs(rect.top - self.top), abs(rect.top - self.bottom),
                abs(rect.bottom - self.top), abs(rect.bottom - self.bottom),
            )
        return (x ** 2 + y ** 2) ** 0.5


class Vector2:
    x: float
    y: float

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class Collider(Rect):
    pass


class AbstractObject:

    def _process(self, delta: float) -> None:
        self.process(delta)

    def process(self, delta: float) -> None:
        return

    def event(self, event) -> None:
        return

    def kill(self):
        del self


class Object(AbstractObject):

    def __init__(self, game: 'Game'):
        self.game: 'Game' = game
        self.game.game_objects.append(self)


class Animation:
    tags: List[int]
    images: List[Surface]
    current: int = 0
    _interval = 0

    def __init__(self, images, interval=100, tags=None, start=0):
        if tags is None:
            tags = [ANIMATION_TAGS['loop']]
        self._interval = self.interval = interval
        self.tags = tags
        self.images = images
        self.current = start

    def image(self):
        length = len(self.images)
        if self.current >= length:
            if ANIMATION_TAGS['loop'] not in self.tags:
                return self.images[-1]
        return self.images[self.current % length].copy()

    def next(self, delta) -> Surface or None:
        self._interval -= delta
        if self._interval <= 0:
            self._interval += self.interval
            self.current += 1


class Sound:
    channel: pygame.mixer.Channel = None

    def set_volume(self, volume: int):
        self.channel.set_volume(volume)

    def get_volume(self):
        self.channel.get_volume()

    def __init__(self, sound: pygame.mixer.Sound):
        self.sound = sound

    def play(self):
        if self.channel is None:
            self.channel = pygame.mixer.find_channel()
        if self.channel is None:
            pygame.mixer.set_num_channels(pygame.mixer.get_num_channels() + 1)
            self.channel = pygame.mixer.find_channel()
        self.channel.play(self.sound)

    def pause(self):
        self.channel.pause()

    def unpause(self):
        self.channel.unpause()

    def stop(self):
        self.channel.stop()


class SimpleSound(Object):
    data: bytes
    sound: simpleaudio.PlayObject

    def __init__(self, game, filename: str, preload: bool = True):
        super().__init__(game)
        self.filename = filename
        if preload:
            self.load()

    def load(self):
        self.data = open(self.filename, 'rb').read()

    def play(self):
        self.sound = simpleaudio.play_buffer(self.data, 2, 2, 44100)

    def stop(self):
        if self.sound:
            self.sound.stop()


class Drawing(Object):
    alpha: int = 255

    def __init__(self, game: 'Game', left=0, top=0, z_index: int = 1):
        super().__init__(game)
        self.z_index: int = z_index
        self.surface: Surface or None = None
        self.rect: Rect = Rect(left, top, 0, 0)

    def get_center(self):
        x = self.rect.x + int(self.rect.w / 2)
        y = self.rect.y + int(self.rect.h / 2)
        return x, y

    def draw(self):
        self.surface.set_alpha(self.alpha)
        self.game.camera.blit(self)


class Sprite(Drawing):

    def __init__(self, game: 'Game', left=0, top=0, size=None):
        super().__init__(game, left, top)
        self.animation: Animation or None = None
        self.ss_size = size

    def set_animation(self, animation: str):
        self.surface: Surface
        self.animation = self.game.resources.animations[animation]
        self.rect.size = self.animation.images[0].get_bounding_rect().size

    def _process(self, delta):
        self.animation.next(delta)
        if self.surface:
            self.rect.size = self.surface.get_bounding_rect().size
        super()._process(delta)

    def draw(self):
        if not self.animation:
            return
        if self.ss_size is None:
            self.surface = self.animation.image()
        else:
            self.surface = pygame.transform.scale(
                self.animation.image(), self.ss_size)
        super().draw()


class UI:
    pass


class Camera(Object, Rect):

    def __init__(self, game: 'Game', viewport_size, x=0, y=0, min_x=0, min_y=0, max_x=None, max_y=None, min_scale=0.5,
                 max_scale=3):
        super().__init__(game)
        self.base_w, self.base_h = viewport_size
        Rect.__init__(self, x, y, self.base_w, self.base_h)
        self.scale: float = 1
        self.min_size = 50
        self.max_size = 500
        self.viewport: Surface = Surface((self.base_w, self.base_h))
        self.ui = Surface((self.base_w, self.base_h), flags=pygame.SRCALPHA)
        self.layers: Dict[Surface] = {}
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

        self.min_scale = min_scale
        self.max_scale = max_scale

    def fill(self, color: pygame.Color):
        self.viewport = Surface(self.size)
        self.ui.fill((0, 0, 0, 0))
        self.viewport.fill(color)

    def blit(self, sprite: Drawing):
        # if sprite.z_index not in self.layers:
        #     self.layers[sprite.z_index] = Surface(self.size)
        rect = sprite.surface.get_rect()
        rect.center = sprite.rect.center
        x, y = 0, 0
        if isinstance(sprite, UI):
            x, y = rect.topleft
            self.ui.blit(sprite.surface, (x, y))
        else:
            x = rect.x - self.x
            y = rect.y - self.y
            # self.layers[sprite.z_index].blit(sprite.surface, (x, y))
            self.viewport.blit(sprite.surface, (x, y))

    def get_viewport(self):
        # size = [i * self.scale for i in self.viewport.get_size()]
        # for i in reversed(tuple(self.layers.values())):
        #     self.viewport.blit(i, (0, 0))
        surf = pygame.transform.scale(self.viewport, self.game.window_size)
        surf.blit(self.ui, (0, 0))
        return surf

    def is_visible(self, sprite: Sprite):
        return sprite.rect.colliderect(self)

    def zoom(self, scale):
        self.zoom_abs(self.scale + scale)

    def zoom_abs(self, scale):
        self.scale = max(self.min_scale, min(self.max_scale, scale))
        if self.max_x is not None:
            self.scale = max(self.scale, self.base_w /
                             (self.max_x - self.min_x))
        if self.max_y is not None:
            self.scale = max(self.scale, self.base_h /
                             (self.max_y - self.min_y))
        self_copy = self.copy()
        self.w = self.base_w / self.scale
        self.h = self.base_h / self.scale
        self.center = self_copy.center
        self.move(0, 0)

    def ui_point_at(self, point):
        return point[0] / self.scale + self.x, point[1] / self.scale + self.y

    def mouse_at(self):
        return self.ui_point_at(self.game.mouse_coord)

    def move(self, x, y):
        self.x = max(self.min_x, self.x + x)
        if self.max_x:
            self.right = min(self.max_x, self.right)
        self.y = max(self.min_y, self.y + y)
        if self.max_y:
            self.bottom = min(self.max_y, self.bottom)


class Game(AbstractObject):
    game_objects: List[AbstractObject] = []

    def __init__(self, window_size, viewport_size, title="", icon="", full_screen: bool = True, tick_rate=60):
        self.window_size = window_size
        flags = pygame.FULLSCREEN if full_screen else 0
        self.screen = pygame.display.set_mode(window_size, flags)
        pygame.display.set_caption(title)
        pygame.init()
        self.camera = Camera(self, viewport_size)
        self.game_objects.append(self)
        self.resources: Resources = Resources()
        self.mouse_coord = ()
        self.keys = ()
        self.tick_rate = tick_rate
        self.load_resources()
        pygame.display.set_icon(self.resources.animations[icon].images[0])

    def create_object(self, obj: AbstractObject):
        self.game_objects.append(obj)

    def load_resources(self):
        pass

    def start(self, fill=None):
        running = True
        clock: pygame.time.Clock = pygame.time.Clock()
        while running:
            self.mouse_coord = pygame.mouse.get_pos()
            self.keys = pygame.key.get_pressed()
            tick = clock.tick(self.tick_rate)
            if fill is not None:
                self.camera.fill(fill)
                self.screen.fill(fill)
            for el in self.game_objects:
                el._process(tick)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    for el in self.game_objects:
                        el.event(event)
            self.screen.blit(self.camera.get_viewport(), (0, 0))
            pygame.display.flip()
        self.quit()

    @staticmethod
    def quit():
        pygame.quit()
        exit()


class Text(Drawing, UI):
    def __init__(self, game: 'Game', font_name: str, text: str = "", color=(0, 0, 0)):
        super().__init__(game)
        self.font: pygame.font.Font = self.game.resources.fonts[font_name]
        self.color = color
        self.set_text(text)

    def set_text(self, text):
        if self.surface:
            self.surface.fill((0, 0, 0, 0))
        self.surface = self.font.render(str(text), 1, self.color)
        self.rect.size = self.surface.get_size()

    def _process(self, delta: float) -> None:
        self.draw()
        super()._process(delta)


class Resources:
    animations: Dict[str, Animation] = {}
    sounds: Dict[str, Sound] = {}
    fonts: Dict[str, pygame.font.Font] = {}
    base_path: str

    def __init__(self, base_path='data'):
        self.base_path = base_path

    def load_animations(self, animations):
        if type(animations) == dict:
            animations = animations.items()
        for i in animations:
            self.load_animation(*i)

    def load_animation(self, animation_name, filenames):
        self.animations[animation_name] = Animation(
            list(map(self.load_image, filenames)))

    def load_font(self, font_name, filename, size=24):
        fullname = os.path.join(self.base_path, filename)
        self.fonts[font_name] = pygame.font.Font(fullname, size)

    def load_sounds(self, sounds):
        if type(sounds) == dict:
            sounds = sounds.items()
        for i in sounds:
            self.load_sound(*i)

    def load_sound(self, sound_name, filename):
        path = os.path.join(self.base_path, filename)
        self.sounds[sound_name] = Sound(pygame.mixer.Sound(path))

    def load_image(self, name, color_key=None):
        fullname = os.path.join(self.base_path, name)
        image = pygame.image.load(fullname)
        if color_key is not None:
            image = image.convert()
            if color_key == -1:
                color_key = image.get_at((0, 0))
            image.set_colorkey(color_key)
        else:
            image = image.convert_alpha()

        return image
