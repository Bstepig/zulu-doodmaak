import random
from typing import List, Iterator

import pygame
import json

from src import core


def get_system_screensize():
    from ctypes import windll
    return windll.user32.GetSystemMetrics(0), windll.user32.GetSystemMetrics(1)


def hex2rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        return tuple(int(h[i:i + 1] * 2, 16) for i in (0, 1, 2))
    elif len(h) == 6:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class Particle(core.Sprite):

    def __init__(self, game, point, animation: str, border_rect=None, dx=0, dy=1, live_time: float = 10000, gravity: float = 0.5, scale=1):
        super().__init__(game)
        self.set_animation(animation)
        self.rect.center = point
        self.live_time = live_time
        self.gravity = gravity
        self.velocity = [dx, dy]
        self.scale = scale
        self.border_rect = border_rect.copy()
        self.ss_size = [int(self.rect.size[0] * scale),
                        int(self.rect.size[1] * scale)]

    def process(self, delta):
        self.live_time -= delta
        if self.live_time <= 0:
            return self.kill()
        self.velocity[1] += self.gravity
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        if self.border_rect is not None:
            self.rect.centerx = min(self.border_rect.right, max(
                self.border_rect.left, self.rect.centerx))
            self.rect.centery = min(self.border_rect.bottom, max(
                self.border_rect.top, self.rect.centery))
        self.draw()


class Particles(core.Object):

    def __init__(self, game, point, animation: str, rect=None, count: int = 10, live_time: float = 10000, gravity: float = 10, min_scale=1, max_scale=5):
        super().__init__(game)
        self.particles: List[Particle] = []
        self.created = False
        self.point = point
        self.rect = rect
        self.live_time = live_time
        self.gravity = gravity
        self.min_scale = min_scale
        self.max_scale = max_scale
        self.animation = animation
        self.count = count

    def set_animation(self, animation):
        [i.set_animation(animation) for i in self.particles]

    def set_count(count):
        self.particles = []
        for i in range(count):
            sprite = core.Sprite(game)
            self.particles.append(sprite)
            sprite.set_animation(animation)

    def play(self):
        self.particles = []
        for i in range(self.count):
            self.particles.append(Particle(self.game, self.point, self.animation, self.rect, dx=random.uniform(
                -3, 3), scale=random.uniform(self.min_scale, self.max_scale), live_time=self.live_time))


class ButtonImage(core.Sprite):

    def __init__(self, game: 'Game', button: 'NativeButton', animation):
        super().__init__(game)
        self.rect = button.rect.copy()
        self.button = button
        self.set_animation(animation)

    def process(self, delta: float) -> None:
        if not self.button.hidden:
            self.rect.center = self.button.rect.center
            self.draw()


class NativeButton(core.Drawing):
    is_hover: bool = False

    def __init__(self, game, rect, color="#ccc", hover_color="#bbb", animation=None, click_callback=None):
        super().__init__(game)
        self.rect = rect
        self.surface = pygame.Surface(self.rect.size)
        self.color = hex2rgb(color)
        self.hover_color = hex2rgb(hover_color)
        self.hidden = False
        self.click_callback = click_callback
        if animation is not None:
            self.sprite = ButtonImage(self.game, self, animation)

    def process(self, delta: float) -> None:
        if self.hidden:
            return
        if self.is_hover:
            self.surface.fill(self.hover_color)
        else:
            self.surface.fill(self.color)
        self.draw()

    def on_click(self):
        if self.click_callback:
            self.click_callback()

    def event(self, event) -> None:
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(self.game.camera.mouse_at()):
                self.is_hover = True
            else:
                self.is_hover = False
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.is_hover:
                    self.on_click()


class Button(NativeButton, core.UI):
    pass


COLLECTED_TYPES = {
    'wood': 0,
    'food': 1,
    'stone': 2
}


class Field(core.Sprite):
    fields = ['field_1', 'field_2']

    def __init__(self, game, left, top):
        super().__init__(game)
        self.set_animation(random.choice(self.fields))
        self.rect.x = self.rect.width * left
        self.rect.y = self.rect.height * top

    def process(self, delta: float) -> None:
        self.draw()


class Accessible(core.Drawing):

    def stop_access(self):
        pass


class Flammable(core.Drawing):
    is_burning: bool = False
    burning_time: int = 0

    def __init__(self, game, left=0, top=0):
        super().__init__(game, left, top)
        self.fire = core.Sprite(self.game)
        self.fire.rect = self.rect
        self.fire.set_animation('fire')

    def process(self, delta: float) -> None:
        if self.is_burning:
            self.burning_time += delta
            self.fire.draw()


class Collected(core.Sprite, Accessible):
    not_collected_animations: List[str]
    not_collected_animation: str

    collected_animations: List[str]
    collected_animation: str

    is_collected: bool = False
    collector = None

    material: int
    collecting_time: int
    recovery_time: int
    left_for_recover: int = 0
    left_for_collect: int = 0
    amount: int

    def __init__(self, game: core.Game, left=0, top=0):
        super().__init__(game, left, top)
        self.not_collected_animation = random.choice(
            self.not_collected_animations)
        self.collected_animation = random.choice(self.collected_animations)
        self.recover()

    def recover(self):
        self.is_collected = False
        self.set_animation(self.not_collected_animation)

    def collect(self):
        self.is_collected = True
        self.stop_collect()
        self.set_animation(self.collected_animation)

    def start_collect(self, collector) -> bool:
        if self.is_collected:
            return False
        self.left_for_collect = self.collecting_time
        self.collector = collector
        return True

    def stop_access(self):
        self.stop_collect()

    def stop_collect(self):
        self.left_for_recover = self.recovery_time
        self.collector = None

    def process(self, delta: float) -> None:
        if self.collector is not None:
            self.left_for_collect -= delta
            if self.left_for_collect <= 0:
                self.collect()
        elif self.is_collected:
            self.left_for_recover -= delta
            if self.left_for_recover <= 0:
                self.recover()
        self.draw()


class Stone(Collected):
    recovery_time: int = 45 * 1000
    material = COLLECTED_TYPES['stone']
    collecting_time: int = 6 * 1000
    amount = 3
    not_collected_animations = ['stone_1', 'stone_2']
    collected_animations = ['stone_clear']

    def __init__(self, game, left=0, top=0):
        super().__init__(game, left, top)


class FoodField(Collected):
    recovery_time: int = 45 * 1000
    material = COLLECTED_TYPES['food']

    def __init__(self, game, left=0, top=0):
        super().__init__(game, left, top)


class SmallFoodField(FoodField):
    collecting_time: int = 6 * 1000
    amount = 3
    not_collected_animations = ['food_field_1']
    collected_animations = ['harvested_food_field_1']


class BigFoodField(FoodField):
    collecting_time: int = 8 * 1000
    amount = 5
    not_collected_animations = ['food_field_2']
    collected_animations = ['harvested_food_field_2']


class Tree(Collected, Flammable):
    recovery_time: int = 45 * 1000
    collected_animations = ['stump']
    material = COLLECTED_TYPES['wood']

    def process(self, delta: float) -> None:
        self.draw()
        if self.burning_time >= 5000:
            self.collect()
            self.burning_time = 0
            self.is_burning = False
        Collected.process(self, delta)
        Flammable.process(self, delta)


class SmallTree(Tree):
    collecting_time: int = 6 * 1000
    amount = 3
    not_collected_animations = ['tree_1', 'tree_3']


class BigTree(Tree):
    collecting_time: int = 8 * 1000
    amount = 5
    not_collected_animations = ['tree_2', 'tree_4']


class Player(core.Object):
    is_defeated: bool = False

    def __init__(self, game, color):
        super().__init__(game)
        self.king: King = None
        self.units: List['Selectable'] = []
        self.color: str = color
        self.resources = [0, 0, 0]

    def add_unit(self, unit: 'Selectable'):
        self.units.append(unit)
        if isinstance(unit, King):
            self.king = unit

    def process(self, delta: float) -> None:
        if self.is_defeated:
            return
        if self.king and self.king.hp <= 0:
            self.is_defeated = True


class Bot(Player):

    def process(self, delta: float) -> None:
        super().process(delta)
        if self.is_defeated:
            return
        for unit in self.units:
            if isinstance(unit, Slave) and unit.goal is None:
                md = -1
                mcol = None
                for collected in self.game.game_objects:
                    if isinstance(collected,
                                  Collected) and collected.collector is None and not collected.is_collected:
                        d = unit.rect.get_distance(collected.rect)
                        if (md == -1 or d < md) and d < 200:
                            md = d
                            mcol = collected
                if mcol:
                    unit.set_goal(mcol)
            elif isinstance(unit, Lancer) and unit.goal is None:
                md = -1
                mcol = None
                for enemy in self.game.game_objects:
                    if isinstance(enemy,
                                  Unit) and enemy.player != self and enemy.hp > 0:
                        d = unit.rect.get_distance(enemy.rect)
                        if (md == -1 or d < md) and d < 100:
                            md = d
                            mcol = enemy
                if mcol:
                    unit.set_goal(mcol)


class Selectable(core.Sprite, Accessible):
    hp: int
    is_selected: bool

    def __init__(self, game, player, max_hp, left=0, top=0):
        super().__init__(game, left, top)
        player.add_unit(self)
        self.hp_panel = core.Drawing(self.game)
        self.is_selected = False
        self.player: Player = player
        self.max_hp: int = max_hp
        self.hp = max_hp
        self.cost = {
            "wood": 0,
            "stone": 0,
            "food": 0
        }

    def process(self, delta: float) -> None:
        self.hp_panel.surface = pygame.Surface((self.rect.w, 5))
        self.hp_panel.rect = self.rect.copy()
        self.hp_panel.rect.size = self.hp_panel.surface.get_size()
        self.hp_panel.rect.y -= 10
        if self.is_selected:
            self.hp_panel.surface.fill((255, 0, 0))
            pygame.draw.rect(self.hp_panel.surface, (0, 255, 0),
                             (0, 0, self.hp / self.max_hp * self.hp_panel.rect.w, 5))
            self.hp_panel.draw()


class Construction(Selectable):

    def __init__(self, game, player: Player, construction_type, max_hp, left=0, top=0):
        super().__init__(game, player, max_hp, left, top)
        self.construction_type: str = construction_type
        animation = f'{self.player.color}_{self.construction_type}'
        self.set_animation(animation)

    def process(self, delta: float) -> None:
        if self.hp <= 0:
            return
        self.draw()
        super().process(delta)


class Barracks(Construction):

    def __init__(self, game, player: Player, left=0, top=0):
        super().__init__(game, player, 'barracks', 120, left, top)
        btn_r = core.Rect(0, 0, 50, 50)
        btn_r.centery = self.rect.centery
        btn_r.x = self.rect.right + 10
        hero = f'{self.player.color}_lancer'
        self.btn = NativeButton(self.game, btn_r, "#fff",
                                "eee", hero, self.buy_lancer)

    def process(self, delta: float) -> None:
        super().process(delta)
        if self.is_selected:
            self.btn.hidden = False
        else:
            self.btn.hidden = True

    def buy_lancer(self):
        self.is_selected = False
        if Lancer.cost['food'] <= self.player.resources[COLLECTED_TYPES["food"]]:
            Lancer(self.game, self.player, left=self.rect.right +
                   30, top=self.rect.centery)
            self.player.resources[COLLECTED_TYPES["food"]
                                  ] -= Lancer.cost['food']
            self.game.set_texts()


class Unit(Selectable):

    def __init__(self, game, player: Player, unit_type, speed, max_hp, left=0, top=0):
        super().__init__(game, player, max_hp, left, top)
        self.goal: Accessible or None = None
        self.target = None
        self.direction = (0, 0)
        self.unit_type: str = unit_type
        self.speed: int = speed
        animation = f'{self.player.color}_{self.unit_type}'
        self.set_animation(animation)
        self.x, self.y = self.rect.topleft

    def process(self, delta: float) -> None:
        if self.hp <= 0:
            if self.goal:
                if isinstance(self.goal, Collected):
                    self.goal.stop_collect()
                self.goal = None
            return
        if self.goal is not None:
            self.follow(self.goal.rect.center)
        if self.target is not None:
            if self.direction is None:
                self.set_target(self.target)
            self.x += self.direction[0] * delta * self.speed / 1000
            self.y += self.direction[1] * delta * self.speed / 1000
            if (self.target[0] - self.x) * self.direction[0] < 0:
                self.x = self.target[0]
                self.direction = 0, self.direction[1]

            if (self.target[1] - self.y) * self.direction[1] < 0:
                self.y = self.target[1]
                self.direction = self.direction[0], 0
        self.rect.x = self.x
        self.rect.y = self.y
        ox = -self.direction[0] * self.rect.size[0]
        oy = -self.direction[1] * self.rect.size[1]
        if ox or oy:
            for i in self.game.game_objects:
                if isinstance(i, Unit) and i != self and self.rect.colliderect(i.rect) and i.direction == (
                        0, 0) and i.goal is None:
                    r = i.rect.copy()
                    r.x += ox
                    r.y += oy
                    i.set_target(r)

        self.draw()
        Selectable.process(self, delta)

    def follow(self, target):
        self.target = target
        x = self.target[0] - self.rect.x
        y = self.target[1] - self.rect.y
        a = (abs(x) + abs(y))
        if a != 0:
            self.direction = x / a, y / a

    def set_target(self, target):
        self.remove_goal()
        self.follow(target)

    def set_goal(self, goal: core.Drawing):
        self.remove_goal()
        self.goal = goal

    def remove_goal(self):
        if self.goal is not None:
            self.goal.stop_access()
            self.goal = None


class Slave(Unit):
    cost = {
        "wood": 0,
        "stone": 0,
        "food": 2
    }

    def __init__(self, game, player, left=0, top=0):
        types = ['slave_1', 'slave_2']
        super().__init__(game, player, random.choice(types), 80, 10, left, top)

    def process(self, delta: float) -> None:
        super().process(delta)
        if self.hp <= 0:
            return
        if self.goal:
            if isinstance(self.goal, Collected):
                if self.goal.collector is not None and self.goal.collector != self:
                    self.target = None
                    self.goal = None
                elif self.rect.colliderect(self.goal.rect):
                    if self.goal.is_collected:
                        self.player.resources[self.goal.material] += self.goal.amount
                        self.game.set_texts()
                        self.target = None
                        self.remove_goal()
                    elif self.goal.collector is None:
                        self.goal.start_collect(self)


class Wizard(Unit):
    cost = {
        "wood": 0,
        "stone": 0,
        "food": 5
    }

    def __init__(self, game, player, left=0, top=0):
        types = ['wizard']
        super().__init__(game, player, random.choice(types), 60, 6, left, top)

    def process(self, delta: float) -> None:
        super().process(delta)
        if self.hp <= 0:
            return
        if self.goal:
            if isinstance(self.goal, Flammable):
                if self.rect.colliderect(self.goal.rect):
                    self.goal.is_burning = True
                    self.target = None
                    self.goal = None


class Lancer(Unit):
    attack: int = 3
    attack_interval: int = 2000
    wait_attack: int = 0
    cost = {
        "wood": 0,
        "stone": 0,
        "food": 5
    }

    def __init__(self, game, player, speed=90, hp=16, types=None, left=0, top=0):
        if types is None:
            types = ['lancer']
        super().__init__(game, player, random.choice(types), speed, hp, left, top)

    def process(self, delta: float) -> None:
        super().process(delta)
        if self.hp <= 0:
            return
        self.wait_attack -= delta

        if self.goal:
            if isinstance(self.goal, Unit):
                if self.goal.hp <= 0:
                    self.goal = None
                elif self.rect.colliderect(self.goal.rect):
                    self.wait_attack -= delta
                    if self.wait_attack <= 0:
                        screm = f'scream_{random.randint(1, 4)}'
                        self.game.resources.sounds[scream].play()
                        self.goal.hp -= self.attack
                        self.wait_attack = self.attack_interval
        else:
            if self.direction == (0, 0):
                md = -1
                mcol = None
                for enemy in self.game.game_objects:
                    if isinstance(enemy,
                                  Unit) and enemy.player != self.player and enemy.hp > 0:
                        d = self.rect.get_distance(enemy.rect)
                        if (md == -1 or d < md) and d < 50:
                            md = d
                            mcol = enemy
                if mcol:
                    self.set_goal(mcol)


class PowerLancer(Lancer):
    attack: int = 5
    cost = {
        "wood": 0,
        "stone": 0,
        "food": 8
    }

    def __init__(self, game, player, left=0, top=0):
        types = ['power_lancer']
        super().__init__(game, player, 80, 20, types, left, top)


class King(Unit):

    def __init__(self, game, player, left=0, top=0):
        types = ['king']
        super().__init__(game, player, random.choice(types), 90, 18, left, top)

    def process(self, delta: float) -> None:
        super().process(delta)
        if self.hp <= 0:
            return


class Selection(core.Drawing):

    def __init__(self, game: 'Generals'):
        self.is_active: bool = False
        self.alpha = 50
        self.start_coord = 0, 0
        self.start_camera = 0, 0
        super().__init__(game)

    def __bool__(self):
        return self.is_active

    def start(self, coord):
        self.is_active = True
        self.start_coord = coord
        self.rect.topleft = self.start_coord

    def end(self):
        self.rect.normalize()
        self.is_active = False

    def event(self, event) -> None:
        real_mouse = self.game.camera.ui_point_at(self.game.mouse_coord)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.start(real_mouse)
        elif event.type == pygame.MOUSEBUTTONUP:
            units = self.game.player.units
            if event.button == 1:
                self.end()
                if self.rect.w >= 15 or self.rect.h >= 15:
                    for sprite in units:
                        if self.rect.colliderect(sprite.rect):
                            sprite.is_selected = True
                        elif not self.game.keys[pygame.K_LSHIFT]:
                            sprite.is_selected = False
                else:
                    selected_units = tuple(
                        filter(lambda x: x.is_selected, units))
                    active = self.game.cursor.hover
                    if isinstance(active, Selectable) and active.player == self.game.player:
                        for i in selected_units:
                            i.is_selected = False
                        active.is_selected = True
                    else:
                        slaves = tuple(
                            filter(lambda x: isinstance(x, Slave), selected_units))
                        wizards = tuple(
                            filter(lambda x: isinstance(x, Wizard), selected_units))
                        lancers = tuple(
                            filter(lambda x: isinstance(x, Lancer), selected_units))
                        ok = True
                        if len(slaves) == 1:
                            active = self.game.cursor.hover
                            if isinstance(active, Collected):
                                ok = False
                                for slave in slaves:
                                    slave.set_goal(active)
                        if len(wizards) == 1:
                            active = self.game.cursor.hover
                            if isinstance(active, Flammable):
                                ok = False
                                for wizard in wizards:
                                    wizard.set_goal(active)
                        if len(lancers):
                            active = self.game.cursor.hover
                            if isinstance(active, Unit):
                                ok = False
                                for lancer in lancers:
                                    lancer.set_goal(active)
                        if ok:
                            for sprite in selected_units:
                                if isinstance(sprite, Unit):
                                    sprite.set_target(real_mouse)
            elif event.button == 3:
                self.end()
                for sprite in units:
                    sprite.is_selected = False

    def process(self, delta: float) -> None:
        if self.is_active:
            end_coord = self.game.camera.ui_point_at(self.game.mouse_coord)
            self.rect.w = abs(end_coord[0] - self.start_coord[0])
            self.rect.h = abs(end_coord[1] - self.start_coord[1])
            self.rect.x = min(end_coord[0], self.start_coord[0])
            self.rect.y = min(end_coord[1], self.start_coord[1])

            self.surface = pygame.Surface((self.rect.w, self.rect.h))

            pygame.draw.rect(self.surface, (255, 255, 255),
                             (0, 0, self.rect.w, self.rect.h), 5)
            self.draw()


class Cursor(core.Sprite, core.UI):

    def __init__(self, game: 'Generals'):
        super().__init__(game)
        self.z_index = 100
        self.hover: core.Drawing = None
        self.set_animation('cursor_default')

    def process(self, delta: float) -> None:
        self.hover = None
        coord = self.game.camera.ui_point_at(self.game.mouse_coord)
        rect = core.Rect(0, 0, 20, 20)
        rect.center = coord
        for sprite in filter(lambda x: isinstance(x, Accessible), reversed(self.game.game_objects)):
            if sprite.rect.colliderect(rect):
                self.hover = sprite
                break
        self.rect.center = self.game.mouse_coord
        if self.rect.x <= 8:
            self.game.camera.move(-4, 0)
        elif self.rect.x >= self.game.window_size[0] - 8:
            self.game.camera.move(4, 0)
        if self.rect.y <= 8:
            self.game.camera.move(0, -4)
        elif self.rect.y >= self.game.window_size[1] - 8:
            self.game.camera.move(0, 4)
        if isinstance(self.hover, Selectable) and self.hover.player == self.game.player:
            self.set_animation('cursor_select')
        else:
            self.set_animation('cursor_default')
        self.draw()


COLLECTED_KEYS = {
    0: SmallTree,
    1: BigTree,
    2: SmallFoodField,
    3: BigFoodField,
    4: Stone
}

CONSTRUCTION_KEYS = {
    0: Barracks,
}

UNITS_KEYS = {
    0: Slave,
    1: Lancer,
    2: PowerLancer,
    3: Wizard,
    4: King
}


class JSONLevelData:
    def __init__(self):
        self.width: int
        self.height: int
        self.collected
        self.units


class LevelJSON(core.Object):

    def __init__(self, game: 'Generals', json_file, tile_size=64):
        super().__init__(game)
        self.tile_size = tile_size
        data: dict = json.loads(json_file)
        self.width = data.get('width')
        self.height = data.get('height')

        camera_pos = data.get('camera_pos')
        zoom = data.get('base_zoom')

        self.game.camera.max_x = self.width
        self.game.camera.max_y = self.height
        self.game.camera.zoom_abs(zoom)
        self.game.camera.topleft = camera_pos

        fields = [[Field(game, i, j) for j in range((self.height + self.tile_size - 1) // self.tile_size)] for i in
                  range((self.width + self.tile_size - 1) // self.tile_size)]
        for i in data.get('collected'):
            pos = i.get('pos')
            type = i.get('type')
            COLLECTED_KEYS[type](game, left=pos[0], top=pos[1])
        for construction in data.get('constructions'):
            player_id = construction.get('player')
            if player_id == 0:
                player = self.game.player
            else:
                player = self.game.bots[player_id % len(self.game.bots)]
            pos = construction.get('pos')
            type = construction.get('type')
            CONSTRUCTION_KEYS[type](game, player, left=pos[0], top=pos[1])
        for unit in data.get('units'):
            player_id = unit.get('player')
            if player_id == 0:
                player = self.game.player
            else:
                player = self.game.bots[player_id % len(self.game.bots)]
            pos = unit.get('pos')
            type = unit.get('type')
            UNITS_KEYS[type](game, player, left=pos[0], top=pos[1])


class Generals(core.Game):

    def __init__(self, window_size, viewport_size, title, icon, full_screen):
        super().__init__(window_size, viewport_size, title, icon, full_screen, 60)
        pygame.font.init()
        self.selection: Selection or None = None
        self.player: Player = Player(self, 'blue')
        self.bots: List[Bot] = [Bot(self, 'red')]
        pygame.mouse.set_visible(False)

        self.main_text = core.Text(self, "Montserrat", '', (255, 255, 255))
        self.wood = core.Text(self, "Montserrat_16", color=(255, 255, 255))
        self.stone = core.Text(self, "Montserrat_16", color=(255, 255, 255))
        self.food = core.Text(self, "Montserrat_16", color=(255, 255, 255))
        self.set_texts()

        self.resources.sounds['music'].play()
        self.resources.sounds['music'].set_volume(0.3)

    def event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 4:  # wheel rolled up
            self.camera.zoom(0.1)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 5:  # wheel rolled down
            self.camera.zoom(-0.1)

    def load_resources(self):
        animations = {
            'cursor_default': ('Cursors/default/1.png',),
            'cursor_select': ('Cursors/select/1.png',
                              'Cursors/select/2.png',
                              'Cursors/select/3.png',
                              'Cursors/select/4.png',
                              ),

            'tree_1': ('Environment/medievalEnvironment_01.png',),
            'tree_2': ('Environment/medievalEnvironment_02.png',),
            'tree_3': ('Environment/medievalEnvironment_03.png',),
            'tree_4': ('Environment/medievalEnvironment_04.png',),
            'stump': ('Environment/medievalEnvironment_05.png',),

            'stone_1': ('Environment/medievalEnvironment_11.png',),
            'stone_2': ('Environment/medievalEnvironment_12.png',),
            'stone_clear': ('Environment/medievalEnvironment_10.png',),

            'food_field_1': ('Tile/medievalTile_54.png',),
            'food_field_2': ('Tile/medievalTile_56.png',),
            'harvested_food_field_1': ('Tile/medievalTile_53.png',),
            'harvested_food_field_2': ('Tile/medievalTile_55.png',),
            'field_1': ('Tile/medievalTile_57.png',),
            'field_2': ('Tile/medievalTile_58.png',),

            'fire': ('Environment/medievalEnvironment_21.png',),

            'red_slave_1': ('Unit/medievalUnit_05.png',),
            'red_slave_2': ('Unit/medievalUnit_06.png',),
            'red_wizard': ('Unit/medievalUnit_07.png',),
            'red_lancer': ('Unit/medievalUnit_08.png',),
            'red_power_lancer': ('Unit/medievalUnit_09.png',),
            'red_king': ('Unit/medievalUnit_10.png',),

            'green_slave_1': ('Unit/medievalUnit_11.png',),
            'green_slave_2': ('Unit/medievalUnit_12.png',),
            'green_wizard': ('Unit/medievalUnit_13.png',),
            'green_lancer': ('Unit/medievalUnit_14.png',),
            'green_power_lancer': ('Unit/medievalUnit_15.png',),
            'green_king': ('Unit/medievalUnit_16.png',),

            'white_slave_1': ('Unit/medievalUnit_17.png',),
            'white_slave_2': ('Unit/medievalUnit_18.png',),
            'white_wizard': ('Unit/medievalUnit_19.png',),
            'white_lancer': ('Unit/medievalUnit_20.png',),
            'white_power_lancer': ('Unit/medievalUnit_21.png',),
            'white_king': ('Unit/medievalUnit_22.png',),

            'blue_slave_1': ('Unit/medievalUnit_23.png',),
            'blue_slave_2': ('Unit/medievalUnit_24.png',),
            'blue_wizard': ('Unit/medievalUnit_01.png',),
            'blue_lancer': ('Unit/medievalUnit_02.png',),
            'blue_power_lancer': ('Unit/medievalUnit_03.png',),
            'blue_king': ('Unit/medievalUnit_04.png',),

            'green_barracks': ('Structure/medievalStructure_21.png',),
            'white_barracks': ('Structure/medievalStructure_21.png',),
            'blue_barracks': ('Structure/medievalStructure_21.png',),
            'red_barracks': ('Structure/medievalStructure_19.png',),

            'icon': ('icon.png',),
        }
        sounds = {
            'music': 'Sounds/music.wav',

            'scream_1': 'Sounds/screams/1.wav',
            'scream_2': 'Sounds/screams/2.wav',
            'scream_3': 'Sounds/screams/3.wav',
            'scream_4': 'Sounds/screams/4.wav',
        }
        self.resources.load_animations(animations)
        self.resources.load_font('Montserrat', 'Montserrat.ttf')
        self.resources.load_font('Montserrat_16', 'Montserrat.ttf', size=16)
        self.resources.load_sounds(sounds)

    def start(self, fill=None):
        self.selection: Selection = Selection(self)
        self.cursor: Cursor = Cursor(self)
        super().start(fill)

    def set_texts(self):
        self.wood.set_text(
            f'Дерева: {self.player.resources[COLLECTED_TYPES["wood"]]}')
        self.food.set_text(
            f'Камня: {self.player.resources[COLLECTED_TYPES["stone"]]}')
        self.stone.set_text(
            f'Еды: {self.player.resources[COLLECTED_TYPES["food"]]}')
        self.wood.rect.topleft = (10, 10)
        self.stone.rect.topleft = (10, 30)
        self.food.rect.topleft = (10, 50)

    def set_main_text(self, text):
        self.main_text.set_text(text)
        self.main_text.rect.center = (
            self.camera.base_w / 2, self.camera.base_h / 2)

    def process(self, delta: float) -> None:
        if self.player.is_defeated:
            self.set_main_text("Ты проиграл")
        elif len(tuple(filter(lambda x: not x.is_defeated, self.bots))) == 0:
            self.set_main_text("Ты выиграл")
        else:
            self.set_main_text("")


RESOLUTIONS = {
    '240': (320, 240),
    '640': (640, 400),
    '720': (1280, 720),
    '768': (1366, 768),
    '900': (1600, 900),
    '1080': (1920, 1080),
}


def main():
    default_screensize = get_system_screensize()
    window_size = default_screensize
    viewport_size = default_screensize
    title = "zulu-doodmaak"
    icon = "icon"
    full_screen = True
    game = Generals(window_size, viewport_size, title, icon, full_screen)
    json_data = open('levels/1.json').read()
    level = LevelJSON(game, json_data)
    game.start((10, 255, 255))
