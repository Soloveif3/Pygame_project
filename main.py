from os import close

import pygame
import os
import sys
import random

from pygame import K_RIGHT, KSCAN_D, KSCAN_S, K_LEFT
from pygame.examples.aliens import Player
from pygame.newbuffer import PyBUF_ND

all_sprites = pygame.sprite.Group()
hitboxes_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()
level_select_sprites = pygame.sprite.Group()
menu_sprites = pygame.sprite.Group()
pause_buttons = pygame.sprite.Group()

size = width, height = 1500, 1000
screen = pygame.display.set_mode(size)
FPS = 60
clock = pygame.time.Clock()


def load_level(filename):
    filename = "data/levels/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    max_width = max(map(len, level_map))

    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


def generate_level(level):
    new_player, x, y = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '#':
                Tile('bricks', x, y)
            elif level[y][x] == '-':
                Tile('floor', x, y)
            elif level[y][x] == '@':
                new_player = Player(player_group, x, y)
    # вернем игрока, а также размер поля в клетках
    return new_player, x, y


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    return image


def terminate():
    pygame.quit()
    sys.exit()


tile_images = {
    'floor': load_image('sprites/interviev/floor.png'),
    'bricks': load_image('sprites/interviev/Bricks.png'),
    'lucky': load_image('sprites/interviev/Lucky_block.png')
}
player_image = load_image('sprites/mario/images.jpg')

tile_width = tile_height = 50


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tiles_group, all_sprites)
        im = pygame.transform.scale(tile_images[tile_type], (tile_height, tile_width))
        self.image = im
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)


# class Player(pygame.sprite.Sprite):
#     def __init__(self, sheet, columns, rows, x, y):
#         super().__init__()
#         self.frames = []
#         self.cut_sheet(sheet, columns, rows)
#         self.cur_frame = 0
#         self.image = pygame.transform.scale(load_image('sprites/mario/images.jpg'), (tile_width, tile_height))
#         # self.image = self.frames[self.cur_frame]
#         self.rect = self.rect.move(x, y)
#
#     def cut_sheet(self, sheet, columns, rows):
#         self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
#         for j in range(rows):
#             for i in range(columns):
#                 frame_location = (self.rect.w * i, self.rect.h * j)
#                 self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))
#
#     def update(self):
#         self.cur_frame = (self.cur_frame + 1) % len(self.frames)
#         self.image = self.frames[self.cur_frame]


class Hitbox(pygame.sprite.Sprite):
    def __init__(self, group, pos_x, pos_y, width, height):
        super().__init__(group, all_sprites)
        self.rect = pygame.rect.Rect(pos_x, pos_y, width, height)
        self.image = pygame.Surface((width, height))


class Player(pygame.sprite.Sprite):
    def __init__(self, group, pos_x, pos_y):
        super().__init__(group, all_sprites)

        self.player_vel_y = 0
        self.player_jump = False
        self.height = 0
        self.width = 0
        self.rotation = 1
        self.speed = 1
        self.image = pygame.transform.scale(player_image, (tile_width - 10, tile_height))
        # self.image.set_colorkey((255, 255, 255))

        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y + 5)

        self.left_hitbox = Hitbox(hitboxes_group, self.rect.x - 1, self.rect.y, 2, tile_height - 10)
        self.right_hitbox = Hitbox(hitboxes_group, self.rect.topright[0], self.rect.y, 2, tile_height - 10)

        # self.head_hitbox = Hitbox(hitboxes_group, self.rect.x + 5, self.rect.y + 5, 140, 10)
        self.leg_hitbox = Hitbox(hitboxes_group, self.rect.bottomleft[0] + 3, self.rect.bottomleft[1], tile_width - 13, 1)
        self.touch_floor_hitbox = Hitbox(hitboxes_group, self.rect.bottomleft[0] - 1, self.rect.bottomleft[1],
                                         tile_width - 10, 1)

    def update(self):
        self.rect = self.rect.move(0, self.player_vel_y)
        if self.player_vel_y < 10:
            self.player_vel_y += 1
        if pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group):
            self.player_jump = False
            self.player_vel_y = 0
        if pygame.sprite.spritecollideany(self.touch_floor_hitbox, tiles_group) and pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group):
            self.rect.y -= 2
        self.hitbox_move()

    def hitbox_move(self):
        self.right_hitbox.rect.x = self.rect.bottomright[0]
        self.right_hitbox.rect.y = self.rect.y + 3

        self.left_hitbox.rect.x = self.rect.x - 1
        self.left_hitbox.rect.y = self.rect.y + 3

        self.touch_floor_hitbox.rect.x = self.rect.x
        self.touch_floor_hitbox.rect.y = self.rect.bottomleft[1] - 1

        self.leg_hitbox.rect.x = self.rect.x
        self.leg_hitbox.rect.y = self.rect.bottomleft[1]

    def move_right(self, direction):
        self.rect = self.rect.move(10, 0)
        if self.rotation == -1:
            self.image = pygame.transform.flip(self.image, True, False)
            self.rotation = 1

    def move_left(self, direction):
        if self.rotation == 1:
            self.image = pygame.transform.flip(self.image, True, False)
            self.rotation = -1
        if not pygame.sprite.spritecollideany(self.left_hitbox, tiles_group):
            self.rect = self.rect.move(-10, 0)

    def jump(self):
        if not self.player_jump:
            self.player_vel_y = -15
            self.player_jump = True


class Button(pygame.sprite.Sprite):
    def __init__(self, group, image='sprites/interviev/Bricks.png', image_var=None, command=None, *args):
        super().__init__(group)
        self.coords = args
        self.command = command
        if image_var:
            self.image_var = pygame.transform.scale(load_image(image_var), (args[2], args[3]))
            self.image_var.set_colorkey((255, 255, 255))
        self.image_norm = load_image(image)
        self.image_norm = pygame.transform.scale(self.image_norm, (args[2], args[3]))
        self.image_norm.set_colorkey((255, 255, 255))
        self.image = self.image_norm
        self.image = pygame.transform.scale(self.image, (args[2], args[3]))

        if args[2]:
            self.rect = pygame.Rect(args)
        else:
            pass
            # self.rect = self.image.get_rect()
        self.rect.x = args[0]
        self.rect.y = args[1]

    def anim(self, time):
        if self.image_var:
            self.image = self.image_var

    def in_mouse(self, pos):
        if self.rect.collidepoint(pos):
            self.anim(clock)
        else:
            self.image = self.image_norm

    def press(self, pos):
        if self.rect.collidepoint(pos):
            print(1)
            self.command()


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dx = 0
        # self.dy = 0

    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        obj.rect.x += self.dx
        # obj.rect.y += self.dy

    # позиционировать камеру на объекте target
    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - width // 2) - 100
        # self.dy = -(target.rect.y + target.rect.h // 2 - height // 2)


def level_select_screen():
    pygame.init()
    running = True
    l1 = Button(level_select_sprites, 'sprites/interface/Play.png', None, main_game, 100, 100, 100, 100)

    while running:
        screen.fill((100, 100, 100, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                l1.in_mouse(pygame.mouse.get_pos())
        level_select_sprites.draw(screen)
        pygame.display.flip()
    pygame.quit()


def start_screen():
    intro_text = ["ЗАСТАВКА", "",
                  "Правила игры",
                  "Если в правилах несколько строк,",
                  "приходится выводить их построчно"]

    pygame.init()
    fon = pygame.transform.scale(load_image('sprites/interface/menu_fon.jpg'), (width, height))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    start = Button(menu_sprites, 'sprites/interface/Play.png', 'sprites/interface/Button_fon.png', main_game, width // 2 - 50,
                   height // 2 - 50, 100, 100)

    while True:
        screen.blit(fon, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                start.press(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                pass
        start.in_mouse(pygame.mouse.get_pos())
        menu_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(10)


def main_game():
    pygame.init()
    running = True
    a = load_level('1_level.txt')
    pl, x, y = generate_level(a)

    camera = Camera()
    # pygame.mixer.music.load('data/sounds/super-mario-saundtrek.mp3')
    # pygame.mixer.music.play()
    # sound1 = pygame.mixer.Sound('boom.wav')

    while running:
        screen.fill((100, 100, 100, 0))
        keys = pygame.key.get_pressed()
        if keys[K_RIGHT]:
            pl.move_right(1)
        if keys[K_LEFT]:
            pl.move_left(1)
        if keys[pygame.K_SPACE]:
            pl.jump()

        camera.update(pl)
        for sprite in all_sprites:
            camera.apply(sprite)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.mixer.music.stop()

        player_group.update()

        player_group.draw(screen)
        tiles_group.draw(screen)
        hitboxes_group.draw(screen)
        pygame.display.flip()
        clock.tick(30)


start_screen()
