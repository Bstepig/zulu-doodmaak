from copy import deepcopy

import pygame
from pygame import Color, Rect
import random


class Puzzle:
    def __init__(self, color: Color, width, height, form):
        self.color = color
        self.width = width
        self.height = height
        self.form = form


class PuzzleI(Puzzle):
    def __init__(self):
        form = (
            (True,),
            (True,),
            (True,),
            (True,)
        )
        super().__init__(Color('orange'), 1, 4, form)


puzzleI = Puzzle(Color('orange'), 1, 4, (
    (True,),
    (True,),
    (True,),
    (True,)
))


class PuzzleT(Puzzle):
    def __init__(self):
        form = (
            (True, True, True),
            (False, True, False),
        )
        super().__init__(Color('yellow'), 3, 2, form)


puzzleT = Puzzle(Color('yellow'), 3, 2, (
    (True, True, True),
    (False, True, False),
))


class PuzzleO(Puzzle):
    def __init__(self):
        form = (
            (True, True),
            (True, True),
        )
        super().__init__(Color('red'), 2, 2, form)


puzzleO = Puzzle(Color('red'), 2, 2, (
    (True, True),
    (True, True),
))


class PuzzleL(Puzzle):
    def __init__(self):
        form = (
            (True, False),
            (True, False),
            (True, True),
        )
        super().__init__(Color('purple'), 2, 3, form)


puzzleL = Puzzle(Color('purple'), 2, 3, (
    (True, False),
    (True, False),
    (True, True),
))


class PuzzleZ(Puzzle):
    def __init__(self):
        form = (
            (True, True, False),
            (False, True, True),
        )
        super().__init__(Color('green'), 3, 2, form)


puzzleZ = Puzzle(Color('green'), 3, 2, (
    (True, True, False),
    (False, True, True),
))


class PuzzleRZ(Puzzle):
    def __init__(self):
        form = (
            (False, True, True),
            (True, True, True),
        )
        super().__init__(Color('blue'), 3, 2, form)


puzzleRZ = Puzzle(Color('blue'), 3, 2, (
    (False, True, True),
    (True, True, True),
))

puzzles = (puzzleI, puzzleL, puzzleO, puzzleRZ, puzzleT, puzzleZ)


class Cell:
    def __init__(self, color: Color = Color('black')):
        self.color = color
        self.used = False


class Board:
    # создание поля
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.board = [[Cell() for i in range(width)] for _ in range(height)]
        # значения по умолчанию
        self.left = 10
        self.top = 10
        self.cell_size = 30
        self.player = 0

    # настройка внешнего вида
    def set_view(self, left, top, cell_size):
        self.left = left
        self.top = top
        self.cell_size = cell_size

    def render(self):
        for i in range(self.height):
            for j in range(self.width):
                self.render_cell(self.board[i][j].color, j, i)

    def render_cell(self, color, x, y):
        x = x * self.cell_size + self.left
        y = y * self.cell_size + self.top
        w = h = self.cell_size
        pygame.draw.rect(screen, color, (x, y, w, h))
        pygame.draw.rect(screen, Color('white'), (x, y, w, h), 1)

    def get_cell(self, mouse_pos):
        x, y = mouse_pos
        x -= self.left
        y -= self.top
        if x < 0 or y < 0 or x > self.width * self.cell_size or y > self.height * self.cell_size:
            return None
        return x // self.cell_size, y // self.cell_size

    def on_click(self, cell_coords):
        pass

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        self.on_click(cell)


class Tetris(Board):
    active_pos = 0, 0
    active: Puzzle

    def __init__(self, width, height, delay):
        super().__init__(width, height)
        self.delay = delay

    def render(self):
        for i in range(self.active.width):
            for j in range(self.active.height):
                if self.active.form[j][i]:
                    self.render_cell(self.active.color, self.active_pos[0] + i, self.active_pos[1])
        pygame.time.wait(self.delay)
        super().render()

    def new_puzzle(self):
        self.active = random.choice(puzzles)
        self.active_pos = 0, 0

    def can_fall(self):
        if self.active_pos[1] >= self.width - 1:
            return False
        for i in range(self.active.height):
            for j in range(self.active.width):
                if self.active[i][j]:
                    if self.board[self.active_pos[1] + i + 1][self.active_pos[0] + j]:
                        return False
        return True

    def next_move(self):
        pass


pygame.init()
size = 800, 600
screen = pygame.display.set_mode(size)

board = Tetris(8, 8, 100)
board.set_view(100, 100, 30)
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                pass
            elif event.key == pygame.K_LEFT:
                pass
            elif event.unicode == ' ':
                board.toggle_life()
    screen.fill((0, 0, 0))
    board.render()
    pygame.display.flip()

pygame.quit()
