import pygame
import os
import sys
import json
import random

from pygame.examples.aliens import Player
from time import sleep

particles_group = pygame.sprite.Group()
decorative_fon = pygame.sprite.Group()

finish_group = pygame.sprite.Group()
decor_group = pygame.sprite.Group()
entity_group = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
hitboxes_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()

menu_sprites = pygame.sprite.Group()
finish_buttons = pygame.sprite.Group()

size = width, height = 1500, 1000
screen_rect = (0, 0, width, height)
screen = pygame.display.set_mode(size)
FPS = 45
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
            elif level[y][x] == '?':
                Tile('lucky', x, y)
            elif level[y][x] == '*':
                Tile('brick_undest', x, y)
            elif level[y][x] == '\"':
                Entity('life', x, y)
            elif level[y][x] == 'O':
                Decor('oblaco', x, y)
            elif level[y][x] == 'T':
                Decor('trava', x, y)
            elif level[y][x] == 'G':
                Gribocheck('grib', x, y)
            elif level[y][x] == 'F':
                Finish('finish', x, y)
            elif level[y][x] == '@':
                new_player = Player(player_group, x * tile_width, y * tile_height)
    # вернем игрока, а также размер поля в клетках
    return new_player, x, y


def load_image(name):
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
    'lucky': load_image('sprites/interviev/Lucky_block.png'),
    'brick_undest': load_image('sprites/interviev/brick_undest.png'),
    'oblaco': load_image('sprites/interviev/oblaco.png'),
    'trava': load_image('sprites/interviev/trava.png')
}

entity_images = {
    'grib': load_image('sprites/interviev/gribocheck.png'),
    'life': load_image('sprites/interviev/life.png')
}

tile_width = tile_height = 50


class Finish(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tiles_group, all_sprites)
        im = pygame.transform.scale(load_image('sprites/interviev/pipe.png'), (tile_width * 2, tile_height * 2))
        self.image = im
        self.x_normal = pos_x * tile_width
        self.y_normal = (pos_y - 1) * tile_height
        self.rect = self.image.get_rect().move(
            self.x_normal, self.y_normal)
        self.finish_hitbox = Hitbox(finish_group, self.rect.x + 30, self.rect.y, tile_width * 2 - 60, 3)

    def __getitem__(self, item):  # для того чтобы проверить что делать с блоком при прикосновенний и тп
        return 0

    def __call__(self, *args):
        if args[1] == 'y':
            print(args[0], self.rect.y, abs(args[0] - self.rect.y))
            return abs(args[0] - self.rect.y)
        else:
            print(args[0], self.rect.x, abs(args[0] - self.rect.x))
            return abs(args[0] - self.rect.x)


class Particle(pygame.sprite.Sprite):
    # сгенерируем частицы разного размера
    fire = [pygame.transform.scale(load_image("sprites/interviev/brick_particle.png"), (10, 10))]
    for scale in (8, 10, 15):
        fire.append(pygame.transform.rotate(pygame.transform.scale(fire[0], (scale, scale)), random.randint(0,
                                                                                                            360)))

    def __init__(self, pos, dx, dy):
        super().__init__(particles_group, all_sprites)
        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()

        # у каждой частицы своя скорость — это вектор
        self.velocity = [dx, dy]
        # и свои координаты
        self.rect.x, self.rect.y = pos

        # гравитация будет одинаковой (значение константы)
        self.gravity = 0.7

    def update(self):
        # применяем гравитационный эффект:
        # движение с ускорением под действием гравитации
        self.velocity[1] += self.gravity
        # перемещаем частицу
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        # убиваем, если частица ушла за экран
        if not self.rect.colliderect(screen_rect):
            self.kill()


def create_particles(position):
    # количество создаваемых частиц
    particle_count = 20
    # возможные скорости
    numbers = range(-5, 6)
    for _ in range(particle_count):
        Particle(position, random.choice(numbers), random.choice(numbers))


class Entity(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y, up=0):
        super().__init__(entity_group, all_sprites)
        im = pygame.transform.scale(entity_images[tile_type], (tile_height, tile_width))

        self.sounds = [pygame.mixer.Sound('data/sounds/mario_jump.mp3'),
                       pygame.mixer.Sound('data/sounds/cinder_block_impact_01.mp3')]
        self.image = im

        self.up = up
        self.rotation = 1
        self.player_jump = False
        self.player_vel_y = 0
        self.x_normal = pos_x * tile_width
        self.y_normal = pos_y * tile_height
        self.rect = self.image.get_rect().move(
            self.x_normal, self.y_normal)
        self.tile_type = tile_type
        self.y_vel = 0
        self.anim_going = False
        self.make_hitboxes()

    def __getitem__(self, item):
        if self.up <= 0:
            entity_group.remove(self)
            return 1, 100
        return 0, 0

    def make_hitboxes(self):
        self.left_hitbox = Hitbox(hitboxes_group, 0, 0, 2, self.rect.height - 3)
        self.right_hitbox = Hitbox(hitboxes_group, 0, 0, 2, self.rect.height - 3)
        self.head_hitbox = Hitbox(hitboxes_group, 0, 0, self.rect.width, 2)
        self.leg_hitbox = Hitbox(hitboxes_group, 0, 0, self.rect.width, 2)

    def hitbox_move(self):
        self.right_hitbox.rect.x = self.rect.bottomright[0]
        self.right_hitbox.rect.y = self.rect.y

        self.left_hitbox.rect.x = self.rect.x
        self.left_hitbox.rect.y = self.rect.y

        self.leg_hitbox.rect.x = self.rect.x
        self.leg_hitbox.rect.y = self.rect.bottomleft[1]

        self.head_hitbox.rect.x = self.rect.x
        self.head_hitbox.rect.y = self.rect.y

    def update(self):
        if self.up <= 0:
            if self.player_vel_y < 10 and self.player_jump:
                self.player_vel_y += 1
            if pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group):
                self.diference = pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group)(self.rect.bottomleft[1],
                                                                                              'y')
                self.rect.y -= self.diference
                self.player_vel_y = 0
                self.player_jump = False
            else:
                self.player_jump = True

            if pygame.sprite.spritecollideany(self.right_hitbox, tiles_group):
                self.rotation = -1
            elif pygame.sprite.spritecollideany(self.left_hitbox, tiles_group):
                self.rotation = 1

            self.rect.x += self.rotation * 3
            self.rect.y += self.player_vel_y
            self.hitbox_move()
        else:
            self.rect.y -= 1
            self.up -= 1


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tiles_group, all_sprites)
        im = pygame.transform.scale(tile_images[tile_type], (tile_height, tile_width))
        self.image = im
        with open('data/Settings/settings.json', 'r') as set:
            data = json.load(set)
            if data["sounds"] == 1:
                self.sounds = [pygame.mixer.Sound('data/sounds/cinder_block_impact_01.mp3'),
                               pygame.mixer.Sound('data/sounds/sfx-6.mp3')]
            else:
                self.sounds = [pygame.mixer.Sound('data/sounds/silent.mp3'),
                               pygame.mixer.Sound('data/sounds/silent.mp3')]
        self.pos_in_level_x = pos_x
        self.pos_in_level_y = pos_y
        self.x_normal = pos_x * tile_width
        self.y_normal = pos_y * tile_height
        self.rect = self.image.get_rect().move(
            self.x_normal, self.y_normal)
        self.tile_type = tile_type
        self.used = False
        self.spawn_animation = tile_height
        self.y_vel = 0
        self.anim_going = False

    def give_random(self):
        self.jump_anim()
        if not self.used:
            if random.choice([1, 2]) == 1:
                Entity('life', self.rect.x / tile_width, self.rect.y // tile_height - 0.1, tile_height)
                self.sounds[1].play()
            else:
                Gribocheck('grib', self.rect.x / tile_width, self.rect.y // tile_height - 0.2, tile_height)
                self.sounds[1].play()
            self.used = True
            self.image = pygame.transform.scale(load_image('sprites/interface/Button_fon.png'),
                                                (tile_height, tile_width))

    def jump_anim(self):
        self.y_vel = -3
        self.anim_going = True

    def destroy_anim(self):
        create_particles(self.rect.center)
        self.sounds[0].play()

    def update(self):
        if self.anim_going:
            self.rect.y += self.y_vel
            self.y_vel += 0.5
        if self.y_vel > 3:
            self.anim_going = False
            self.rect.y = self.y_normal

    def do_smth(self, do, speed):
        if do == 'destroy':
            if speed < -5:
                self.destroy_anim()
                tiles_group.remove(self)
            elif -5 <= speed < 0:
                self.jump_anim()
        elif do == 'random':
            if speed < 0:
                self.give_random()

    def __getitem__(self, item):  # для того чтобы проверить что делать с блоком при прикосновенний и тп
        if self.tile_type == 'bricks':
            self.do_smth('destroy', item)
        elif self.tile_type == 'lucky':
            self.do_smth('random', item)

    def __call__(self, *args):
        if args[1] == 'y':
            print(args[0], self.rect.y, abs(args[0] - self.rect.y))
            return abs(args[0] - self.rect.y)
        else:
            print(args[0], self.rect.x, abs(args[0] - self.rect.x))
            return abs(args[0] - self.rect.x)


class Decor(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(decor_group, all_sprites)
        im = pygame.transform.scale(tile_images[tile_type], (tile_width * 2, tile_height))
        self.image = im
        self.x_normal = pos_x * tile_width
        self.y_normal = pos_y * tile_height
        self.rect = self.image.get_rect().move(
            self.x_normal, self.y_normal)


class Gribocheck(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y, up=0):
        super().__init__(entity_group, all_sprites)
        self.im = pygame.transform.scale(entity_images[tile_type], (tile_height, tile_width))
        with open('data/Settings/settings.json', 'r') as set:
            data = json.load(set)
            if data["sounds"] == 1:
                self.sounds = [pygame.mixer.Sound('data/sounds/sfx-15.mp3'),
                               pygame.mixer.Sound('data/sounds/sfx-17.mp3')]
            else:
                self.sounds = [pygame.mixer.Sound('data/sounds/silent.mp3'),
                               pygame.mixer.Sound('data/sounds/silent.mp3')]

        self.trup = 0
        self.image = self.im
        self.frame_time = 0

        self.up = up
        self.rotation = random.choice([-1, 1])
        self.player_jump = False
        self.player_vel_y = 0
        self.x_normal = pos_x * tile_width
        self.y_normal = pos_y * tile_height
        self.rect = self.image.get_rect().move(
            self.x_normal, self.y_normal)
        self.tile_type = tile_type
        self.y_vel = 0

        self.make_hitboxes()

    def __getitem__(self, item):
        if self.trup <= 0 and self.up <= 0:
            if item == 'kill':
                self.trup = 20
                self.image = pygame.transform.scale(load_image('sprites/interviev/gribocheck_.png'),
                                                    (tile_height, tile_width))
                self.sounds[1].play()
                return 0, 150
            else:
                self.sounds[0].play()
                return -1, -50
        return 0, 0

    def make_hitboxes(self):
        self.left_hitbox = Hitbox(hitboxes_group, 0, 0, 2, self.rect.height - 3)
        self.right_hitbox = Hitbox(hitboxes_group, 0, 0, 2, self.rect.height - 3)
        self.head_hitbox = Hitbox(hitboxes_group, 0, 0, self.rect.width, 2)
        self.leg_hitbox = Hitbox(hitboxes_group, 0, 0, self.rect.width, 2)

    def hitbox_move(self):
        self.right_hitbox.rect.x = self.rect.bottomright[0]
        self.right_hitbox.rect.y = self.rect.y

        self.left_hitbox.rect.x = self.rect.x
        self.left_hitbox.rect.y = self.rect.y

        self.leg_hitbox.rect.x = self.rect.x
        self.leg_hitbox.rect.y = self.rect.bottomleft[1]

        self.head_hitbox.rect.x = self.rect.x
        self.head_hitbox.rect.y = self.rect.y

    def anim(self):
        if self.frame_time < 20:
            self.image = pygame.transform.flip(self.im, True, False)
        else:
            self.image = self.im
        if self.frame_time >= 40:
            self.frame_time = 0

    def update(self):
        if self.trup <= 0:
            if self.up <= 0:
                if self.player_vel_y < 10 and self.player_jump:
                    self.player_vel_y += 1
                if pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group):
                    self.diference = pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group)(
                        self.rect.bottomleft[1], 'y')
                    self.rect.y -= self.diference
                    self.player_vel_y = 0
                    self.player_jump = False
                else:
                    self.player_jump = True

                if pygame.sprite.spritecollideany(self.right_hitbox, tiles_group):
                    self.rotation = -1
                elif pygame.sprite.spritecollideany(self.left_hitbox, tiles_group):
                    self.rotation = 1

                self.frame_time += 3
                self.rect.x += self.rotation * 3
                self.rect.y += self.player_vel_y
                self.hitbox_move()
                self.anim()
            else:
                self.rect.y -= 1
                self.up -= 1
        else:
            self.trup -= 1
            if self.trup == 1:
                self.kill()


class Hitbox(pygame.sprite.Sprite):
    def __init__(self, group, pos_x, pos_y, width, height):
        super().__init__(group, all_sprites)
        self.rect = pygame.rect.Rect(pos_x, pos_y, width, height)
        self.image = pygame.Surface((width, height))


class Player(pygame.sprite.Sprite):
    def __init__(self, group, pos_x, pos_y):
        super().__init__(group, all_sprites)
        with open('data/Settings/settings.json', 'r') as set:
            data = json.load(set)
            if data["sounds"] == 1:
                self.sounds = [pygame.mixer.Sound('data/sounds/mario_jump.mp3')]
                self.sounds[0].set_volume(0.3)
            else:
                self.sounds = [pygame.mixer.Sound('data/sounds/silent.mp3')]
        # все что связано с анимкой
        self.frame_time = 0
        self.frames = []
        self.cut_frames()
        self.cur_frame = 0

        # очки и жизни
        self.score = 1
        self.lives = 1
        self.in_losing = True
        self.level_time = 0
        self.player_win_anim = False
        self.end_level = False

        # уязвим ли игрок сейчас
        self.invisibility = False
        self.invisibility_time = 0
        self.finish_anim = 0

        # параметры движения
        self.touch_floor = False
        self.diference = 0
        self.player_speed = 0
        self.player_vel_y = 0
        self.player_jump = False

        self.height = 0
        self.width = 0
        self.rotation = 0
        self.image = self.frames[-2]
        self.image.set_colorkey((255, 255, 255))

        self.rect = pygame.rect.Rect(pos_x, pos_y, tile_width, tile_height)
        self.make_hitboxes()

    def make_hitboxes(self):
        self.left_hitbox = Hitbox(hitboxes_group, 0, 0, 2, tile_height - 13)
        self.right_hitbox = Hitbox(hitboxes_group, 0, 0, 2, tile_height - 13)
        self.head_hitbox = Hitbox(hitboxes_group, 0, 0, tile_width - 10, 1)
        self.leg_hitbox = Hitbox(hitboxes_group, 0, 0, tile_width - 10, 1)
        self.kill_hitbox = Hitbox(hitboxes_group, 0, 0, self.rect.width - 10, tile_height // 2 - 20)

    def cut_frames(self):  # вырезка картинок для анимаций
        self.frames.append(pygame.transform.scale(load_image('sprites/mario/injump.png'), (tile_width, tile_height)))
        self.frames.append(pygame.transform.scale(load_image('sprites/mario/lose.png'), (tile_width, tile_height)))
        self.frames.append(pygame.transform.scale(load_image('sprites/mario/run_1.png'), (tile_width, tile_height)))
        self.frames.append(pygame.transform.scale(load_image('sprites/mario/run_2.png'), (tile_width, tile_height)))
        self.frames.append(pygame.transform.scale(load_image('sprites/mario/run_3.png'), (tile_width, tile_height)))
        self.frames.append(pygame.transform.scale(load_image('sprites/mario/stay.png'), (tile_width, tile_height)))
        self.frames.append(pygame.transform.scale(load_image('sprites/mario/turn.png'), (tile_width, tile_height)))

    def finish(self):
        return self.end_level

    def update(self, keys=None):
        if self.finish_anim > 0:
            self.rect.y += 1
            self.finish_anim -= 1
            self.player_win_anim = True

        elif self.finish_anim <= 0 and self.player_win_anim:
            self.end_level = True

        elif self.in_losing:
            if self.player_vel_y < 18 and self.player_jump:
                self.player_vel_y += 1
            # проверка на столкновения
            self.floor()

            # проверка на удар с потолком
            if pygame.sprite.spritecollideany(self.head_hitbox, tiles_group):
                pygame.sprite.spritecollideany(self.head_hitbox, tiles_group)[self.player_vel_y]
                self.player_vel_y = 1
            # проверка на прикосновение с землей
            if pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group):
                self.diference = pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group)(self.rect.bottomleft[1],
                                                                                              'y')
                self.rect.y -= self.diference
                self.player_vel_y = 0
                self.player_jump = False
            else:
                self.player_jump = True
                self.touch_floor = False
            do = False
            if pygame.sprite.spritecollideany(self, entity_group) and pygame.sprite.spritecollideany(self.kill_hitbox,
                                                                                                     entity_group):
                do = pygame.sprite.spritecollideany(self.kill_hitbox, entity_group)['kill']
                if do[0] == 0 and do[1] != 0:
                    self.player_vel_y = -3
                if do[0] < 0:
                    if not self.invisibility:
                        self.lives += do[0]
                        self.invisibility_time = 100
                        self.score += do[1]
                else:
                    self.lives += do[0]
                    self.score += do[1]
            elif pygame.sprite.spritecollideany(self, entity_group):
                if not do:
                    do = pygame.sprite.spritecollideany(self, entity_group)['']
                if do[0] < 0:
                    if not self.invisibility:
                        self.lives += do[0]
                        self.invisibility_time = 100
                        self.score += do[1]
                else:
                    self.lives += do[0]
                    self.score += do[1]

            if self.invisibility_time <= 0:
                self.invisibility = False
            else:
                self.invisibility = True
            if self.invisibility_time > 0:
                self.invisibility_time -= 1
            self.hitbox_move()
            # если игрок(жмет кнопки) не идет, то он замедляется
            if not (keys[pygame.K_RIGHT] or keys[pygame.K_LEFT]):
                if self.player_speed > 0:
                    self.player_speed -= 1
                elif self.player_speed < 0:
                    self.player_speed += 1

            self.walls()
            self.level_time += 1
            # смещение после всех проверок

            self.rect.x += self.player_speed
            self.rect.y += self.player_vel_y
            self.hitbox_move()
            self.anim(keys)  # анимация (смена фреима)
        else:
            self.stay_lose -= 1
            if self.stay_lose <= 0:
                self.rect.y += self.player_vel_y
                self.player_vel_y += 0.4

    def get_stats(self):
        return self.lives, self.score, self.level_time

    def check_finish(self):
        if pygame.sprite.spritecollideany(self.leg_hitbox, finish_group):
            self.finish_anim = tile_height + 5
            self.player_win = True

    def rotated(self):
        if self.rotation < 0:
            self.image = pygame.transform.flip(self.image, True, False)

    def anim(self, keys):
        if self.player_jump:
            self.image = self.frames[0]
            self.rotated()
        elif (keys[pygame.K_RIGHT] and self.player_speed < 0) or keys[pygame.K_LEFT] and self.player_speed > 0:
            self.image = self.frames[-1]
            self.rotated()
        elif self.player_speed != 0:
            if self.frame_time > 3:
                self.cur_frame = (self.cur_frame + 1) % 4
                self.image = self.frames[2:6][self.cur_frame]
                self.frame_time = 0
                self.rotated()
            self.frame_time += 1
        else:
            self.image = self.frames[-2]
            self.rotated()
        if self.invisibility_time > 0:
            if self.invisibility_time % 10 == 0 or self.invisibility_time % 10 == 5:
                self.image = load_image('sprites/mario/None.png')

    def hitbox_move(self):
        self.right_hitbox.rect.x = self.rect.bottomright[0]
        self.right_hitbox.rect.y = self.rect.y + 6

        self.left_hitbox.rect.x = self.rect.x - 1
        self.left_hitbox.rect.y = self.rect.y + 6

        self.leg_hitbox.rect.x = self.rect.x + 5
        self.leg_hitbox.rect.y = self.rect.bottomleft[1]

        self.head_hitbox.rect.x = self.rect.x + 5
        self.head_hitbox.rect.y = self.rect.y

        self.kill_hitbox.rect.x = self.rect.x + 5
        self.kill_hitbox.rect.y = self.rect.y + tile_height // 2 + 20

    def floor(self):
        if pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group):
            self.diference = pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group)(self.rect.bottomleft[1], 'y')
            self.rect.y -= self.diference + 0.2
            self.player_vel_y = 0
            self.player_jump = False
        else:
            self.player_jump = True

    def lose(self):
        self.in_losing = False
        self.player_vel_y = -10
        self.stay_lose = 50
        self.image = self.frames[1]

    def walls(self):
        if pygame.sprite.spritecollideany(self.right_hitbox, tiles_group) and self.player_speed > 0:
            diference = pygame.sprite.spritecollideany(self.right_hitbox, tiles_group)(self.rect.x + tile_width, 'x')
            self.rect.x -= diference
            self.player_speed = 0

        if pygame.sprite.spritecollideany(self.left_hitbox, tiles_group) and self.player_speed < 0:
            diference = pygame.sprite.spritecollideany(self.left_hitbox, tiles_group)(self.rect.x - tile_width, 'x')
            self.rect.x += diference
            self.player_speed = 0

    def move_right(self):
        if self.finish_anim > 0:
            pass
        elif self.in_losing:
            self.floor()
            self.hitbox_move()
            if not pygame.sprite.spritecollideany(self.right_hitbox, tiles_group):
                if self.player_speed < 10:
                    self.player_speed += 1
            else:
                if pygame.sprite.spritecollideany(self.right_hitbox, tiles_group)(self.rect.bottomright[1], 'x'):
                    diference = pygame.sprite.spritecollideany(self.right_hitbox, tiles_group)(self.rect.x + tile_width,
                                                                                               'x')
                    self.rect.x -= diference
                    self.player_speed = 0

                # self.rect = self.rect.move(self.player_speed, 0)
            self.rotation = 1
            self.hitbox_move()

    def move_left(self):
        if self.finish_anim > 0:
            pass
        elif self.in_losing:
            self.floor()
            self.hitbox_move()
            if not pygame.sprite.spritecollideany(self.left_hitbox, tiles_group):
                if self.player_speed > -10:
                    self.player_speed -= 1
            else:
                if pygame.sprite.spritecollideany(self.left_hitbox, tiles_group)(self.rect.bottomleft[1], 'x'):
                    diference = pygame.sprite.spritecollideany(self.left_hitbox, tiles_group)(self.rect.x - tile_width,
                                                                                              'x')
                    self.rect.x += diference
                    self.player_speed = 0

                    # self.rect = self.rect.move(self.player_speed, 0)
            self.rotation = -1
            self.hitbox_move()

    def jump(self):
        if self.finish_anim > 0:
            pass
        elif self.in_losing:
            if not self.player_jump:
                self.player_vel_y -= 20
                self.rect.y -= 2
                self.player_jump = True
                self.sounds[0].play()
            self.hitbox_move()


class Button(pygame.sprite.Sprite):
    def __init__(self, group, image='sprites/interviev/Bricks.png', image_var=None, command=None, level=None, *args):
        super().__init__(group)
        self.coords = args
        self.command = command
        self.level = level
        self.sound = pygame.mixer.Sound('data/sounds/sfx-4.mp3')
        if image_var:
            self.image_var = pygame.transform.scale(load_image(image_var), (args[2], args[3]))
        else:
            self.image_var = pygame.transform.scale(load_image(image), (args[2], args[3]))
        self.image_norm = load_image(image)
        self.image_norm = pygame.transform.scale(self.image_norm, (args[2], args[3]))
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
            self.anim(0)
        else:
            self.image = self.image_norm

    def press(self, pos):
        if self.rect.collidepoint(pos):
            if self.level:
                self.sound.play()
                self.command(self.level)
            else:
                self.sound.play()
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
    level_select_sprites = pygame.sprite.Group()
    running = True
    with open('data/levels/level_results.json', 'r') as settings_file:
        data = json.load(settings_file)
    levels_info_texts = list()
    for i in range(1, 6):
        levels_info_texts.append(list())
        levels_info_texts[i - 1].append(pygame.font.Font('data/Settings/press-start-k.ttf', 30).render(str(data[f"{i}_level.txt"]["score"]), False, (255, 218, 185)))
        levels_info_texts[i - 1].append(pygame.font.Font('data/Settings/press-start-k.ttf', 30).render(str(data[f"{i}_level.txt"]["time"]), False, (175, 238, 238)))
        levels_info_texts[i - 1].append(pygame.font.Font('data/Settings/press-start-k.ttf', 30).render(str(data[f"{i}_level.txt"]["result"]), False, (255, 69, 0)))
    fon = pygame.transform.scale(load_image('sprites/interface/fon.png'), (width, height))
    l_x = range(100, 1350, 250)
    l1 = Button(level_select_sprites, 'sprites/interface/image_2025-02-25_22-27-22.png',
                'sprites/interface/Play.png', main_game, '1_level.txt',
                100,
                300, 150, 150)
    l2 = Button(level_select_sprites, 'sprites/interface/image_2025-02-25_22-29-59.png',
                'sprites/interface/Play.png', main_game, '2_level.txt',
                350,
                300, 150, 150)
    l3 = Button(level_select_sprites, 'sprites/interface/image_2025-02-25_22-32-51.png',
                'sprites/interface/Play.png', main_game, '3_level.txt',
                600,
                300, 150, 150)
    l4 = Button(level_select_sprites, 'sprites/interface/image_2025-02-25_22-37-35.png',
                'sprites/interface/Play.png', main_game, '4_level.txt',
                850,
                300, 150, 150)
    l5 = Button(level_select_sprites, 'sprites/interface/image_2025-02-25_22-40-36.png',
                'sprites/interface/Play.png', main_game, '5_level.txt',
                1100,
                300, 150, 150)

    while running:
        screen.blit(fon, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                start_screen()
            if event.type == pygame.MOUSEBUTTONDOWN:
                l1.press(event.pos)
                l2.press(event.pos)
                l3.press(event.pos)
                l4.press(event.pos)
                l5.press(event.pos)
        l1.in_mouse(pygame.mouse.get_pos())
        l2.in_mouse(pygame.mouse.get_pos())
        l3.in_mouse(pygame.mouse.get_pos())
        l4.in_mouse(pygame.mouse.get_pos())
        l5.in_mouse(pygame.mouse.get_pos())
        level_select_sprites.draw(screen)
        for y in range(len(l_x)):
            for x in range(3):
                screen.blit(levels_info_texts[y][x], (l_x[y], 500 + x * 30))
        pygame.display.flip()
    pygame.quit()


def turn_sounds():
    with open('data/Settings/settings.json', 'r') as settings_file:
        data = json.load(settings_file)
    with open('data/Settings/settings.json', 'w') as settings_file:
        if data["sounds"] == 1:
            data["sounds"] = 0
        elif data["sounds"] == 0:
            data["sounds"] = 1
        json.dump(data, settings_file, indent=2)


def turn_music():
    with open('data/Settings/settings.json', 'r') as settings_file:
        data = json.load(settings_file)
    with open('data/Settings/settings.json', 'w') as settings_file:
        if data["music"] == 1:
            data["music"] = 0
        elif data["music"] == 0:
            data["music"] = 1
        json.dump(data, settings_file, indent=2)


def clear_results():
    data = {
        "1_level.txt": {
            "score": 0,
            "time": 0,
            "result": 0
        },
        "2_level.txt": {
            "score": 0,
            "time": 0,
            "result": 0
        },
        "3_level.txt": {
            "score": 0,
            "time": 0,
            "result": 0
        },
        "4_level.txt": {
            "score": 0,
            "time": 0,
            "result": 0
        },
        "5_level.txt": {
            "score": 0,
            "time": 0,
            "result": 0
        }
    }
    with open('data/levels/level_results.json', 'w') as lv:
        json.dump(data, lv, indent=2)


def settings_screen():
    settings_sprites = pygame.sprite.Group()
    running = True
    font = pygame.font.Font('data/Settings/press-start-k.ttf', 40)

    reset_results_text = font.render(f'reset results', False, (255, 255, 255))
    turn_s_text = font.render(f'turn sounds', False, (255, 255, 255))
    turn_m_text = font.render(f'turn music', False, (255, 255, 255))

    fon = pygame.transform.scale(load_image('sprites/interface/fon.png'), (width, height))
    screen.blit(fon, (0, 0))
    sounds_button = Button(settings_sprites, 'sprites/interface/image_2025-02-25_22-03-12.png', False,
                           turn_sounds, None,
                           width // 2 - 200,
                           height // 2 - 250, 100, 100)
    music_button = Button(settings_sprites, 'sprites/interface/image_2025-02-25_22-03-12.png', False,
                          turn_music, None,
                          width // 2 - 200,
                          height // 2 - 100, 100, 100)
    reset_results = Button(settings_sprites, 'sprites/interface/image_2025-02-25_21-39-54.png', False,
                           clear_results, None,
                           width // 2 - 200,
                           height // 2 + 50, 100, 100)
    continue_but = Button(settings_sprites, 'sprites/interface/image_2025-02-25_21-50-38.png',
                          'sprites/interface/image_2025-02-25_21-52-20.png',
                          start_screen, None, width // 2 + 500, height // 2 + 350, 100, 100)
    while running:
        screen.blit(fon, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                continue_but.press(event.pos)
                reset_results.press(event.pos)
                music_button.press(event.pos)
                sounds_button.press(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                pass
        continue_but.in_mouse(pygame.mouse.get_pos())
        sounds_button.in_mouse(pygame.mouse.get_pos())
        music_button.in_mouse(pygame.mouse.get_pos())
        settings_sprites.draw(screen)
        screen.blit(reset_results_text, (width // 2 - 50, height // 2 + 70))
        screen.blit(turn_m_text, (width // 2 - 50, height // 2 - 70))
        screen.blit(turn_s_text, (width // 2 - 50, height // 2 - 230))
        pygame.display.flip()


def start_screen():
    pygame.init()
    fon = pygame.transform.scale(load_image('sprites/interface/fon.png'), (width, height))
    screen.blit(fon, (0, 0))
    with open('data/Settings/settings.json', 'r') as set:
        data = json.load(set)
        if data["music"] == 1:
            pygame.mixer.music.load('data/sounds/mario-para-pa-para-pam-punk.mp3')
        else:
            pygame.mixer.music.load('data/sounds/silent.mp3')
    pygame.mixer.music.play(-1)

    start = Button(menu_sprites, 'sprites/interface/Play.png', False,
                   level_select_screen, None,
                   width // 2 + 50,
                   height // 2 - 50, 100, 100)
    settings_but = Button(menu_sprites, 'sprites/interface/image_2025-02-25_22-03-12.png',
                          'sprites/interface/image_2025-02-25_22-17-50.png',
                          settings_screen, None,
                          width // 2 - 100,
                          height // 2 - 50, 100, 100)

    while True:
        screen.blit(fon, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                start.press(event.pos)
                settings_but.press(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                pass
        start.in_mouse(pygame.mouse.get_pos())
        settings_but.in_mouse(pygame.mouse.get_pos())
        menu_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(10)


def draw_text(screen, text, number, *args):
    font = pygame.font.Font('data/Settings/press-start-k.ttf', 40)
    y = args[1]
    x = args[0]
    for el in (text, number):  # вывод и настроика текста и значение (хп, очки)
        text = font.render(f'{el}', False, (255, 255, 255))
        text.set_colorkey((0, 0, 0))
        text_x = x
        text_y = y
        x += args[2]
        y += args[3]
        screen.blit(text, (text_x, text_y))


def draw_groups(screen, texts):
    decor_group.draw(screen)
    entity_group.draw(screen)
    particles_group.draw(screen)
    # hitboxes_group.draw(screen)
    player_group.draw(screen)
    tiles_group.draw(screen)
    for i in range(0, len(texts), 2):
        draw_text(screen, texts[i], texts[i + 1], i * 200 + 50, 50, 40, 40)


def finish_screen(score, time, level):
    running = True
    level_int = int(level.split('_')[0])
    font = pygame.font.Font('data/Settings/press-start-k.ttf', 60)

    text_score = font.render(f'score: {score}', False, (255, 255, 255))
    text_time = font.render(f'time: {time}', False, (255, 255, 255))

    restart_button = Button(finish_buttons, 'sprites/interface/image_2025-02-25_21-39-54.png',
                            'sprites/interface/image_2025-02-25_21-53-47.png',
                            main_game, level, width // 2 - 50, height // 2 + 200, 100, 100)
    select_level = Button(finish_buttons, 'sprites/interface/image_2025-02-25_21-50-38.png',
                          'sprites/interface/image_2025-02-25_21-52-20.png',
                          start_screen, None, width // 2 - 350, height // 2 + 150, 100, 100)
    if level_int != 5:
        continue_button = Button(finish_buttons, 'sprites/interface/Play.png', None,
                                 main_game, f'{level_int + 1}_level.txt',
                                 width // 2 + 250, height // 2 + 150, 100, 100)

    new_rec = False
    with open('data/levels/level_results.json', 'r') as last_level_result:
        data = json.load(last_level_result)

        last_score = data[level]["score"]
        last_time = data[level]["time"]
        last_result = data[level]["result"]
        result = int(score * (300 / time))

        result_text = font.render(f'result: {result}', False, (255, 255, 255))
        if result >= last_result:
            data[level]["score"] = score
            data[level]["time"] = time
            data[level]["result"] = result
            new_rec = True
            with open('data/levels/level_results.json', 'w') as level_result:
                json.dump(data, level_result, indent=2)
    if new_rec:
        text_new_rec = font.render(f'new record', False, (255, 200, 200))

    while running:
        screen.fill((92, 148, 250))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                restart_button.press(event.pos)
                select_level.press(event.pos)
                if level_int != 5:
                    continue_button.press(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                pass
        restart_button.in_mouse(pygame.mouse.get_pos())
        select_level.in_mouse(pygame.mouse.get_pos())
        if level_int != 5:
            continue_button.in_mouse(pygame.mouse.get_pos())
        screen.blit(text_score, (400, 200))
        screen.blit(text_time, (450, 270))
        screen.blit(result_text, (400, 340))
        if new_rec:
            screen.blit(text_new_rec, (400, 430))
        finish_buttons.draw(screen)
        pygame.display.flip()


def main_game(level):
    pygame.init()
    running = True
    in_losing = True
    level = level
    a = load_level(level)
    pl, x, y = generate_level(a)

    camera = Camera()

    # загружаем звуки
    with open('data/Settings/settings.json', 'r') as set:
        data = json.load(set)
        if data["music"] == 1:
            pygame.mixer.music.load('data/sounds/super-mario-saundtrek.mp3')
            pygame.mixer.music.play(-1)
            lose_music = pygame.mixer.Sound('data/sounds/mario-lose.mp3')
            win_music = pygame.mixer.Sound('data/sounds/super-mario-fanfara-okonchaniya-urovnya-muzyka-iz-igry-nintendo.mp3')
        else:
            pygame.mixer.music.load('data/sounds/silent.mp3')
            pygame.mixer.music.play(-1)
            lose_music = pygame.mixer.Sound('data/sounds/silent.mp3')
            win_music = pygame.mixer.Sound('data/sounds/silent.mp3')
    # mario_jump_sound = pygame.mixer.Sound('data/sounds/mario_jump.mp3')  # прыжок
    # destroying_sound =   # разрушение
    # sounds = [mario_jump_sound, destroying_sound]
    while running:
        screen.fill((92, 148, 252, 0))
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            pl.move_right()
        elif keys[pygame.K_LEFT]:
            pl.move_left()
        if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
            pl.jump()
        if pl.rect.y > height:
            running = False
            player_group.empty()
            tiles_group.empty()
            decor_group.empty()
            hitboxes_group.empty()
            entity_group.empty()
            all_sprites.empty()
            finish_buttons.empty()
            finish_group.empty()
            pygame.mixer.music.stop()
            if in_losing:
                lose_music.play()
            sleep(1)
            main_game(level)

        camera.update(pl)
        for sprite in all_sprites:
            camera.apply(sprite)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
                pl.check_finish()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                player_group.empty()
                tiles_group.empty()
                decor_group.empty()
                hitboxes_group.empty()
                entity_group.empty()
                all_sprites.empty()
                finish_buttons.empty()
                finish_group.empty()
                pygame.mixer.music.stop()
                start_screen()
            if event.type == pygame.QUIT:
                running = False
                player_group.empty()
                tiles_group.empty()
                decor_group.empty()
                hitboxes_group.empty()
                entity_group.empty()
                all_sprites.empty()
                finish_buttons.empty()
                finish_group.empty()
                pygame.mixer.music.stop()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                running = False
                player_group.empty()
                tiles_group.empty()
                decor_group.empty()
                hitboxes_group.empty()
                entity_group.empty()
                all_sprites.empty()
                finish_buttons.empty()
                finish_group.empty()
                pygame.mixer.music.stop()
                main_game(level)

        tiles_group.update()
        player_group.update(keys)
        entity_group.update()
        particles_group.update()

        l_s = pl.get_stats()

        if l_s[0] == 0 and in_losing:
            pl.lose()
            in_losing = False
            pygame.mixer.music.stop()
            lose_music.play()
        if pl.finish():
            running = False
            player_group.empty()
            tiles_group.empty()
            decor_group.empty()
            hitboxes_group.empty()
            entity_group.empty()
            all_sprites.empty()
            finish_buttons.empty()
            finish_group.empty()
            pygame.mixer.music.stop()
            win_music.play()
            finish_screen(l_s[1], l_s[2] // FPS, level)

        draw_groups(screen, ('Score', l_s[1],
                             'Lives', l_s[0],
                             'Time', l_s[2] // FPS,
                             'level', level.split('_')[0]))

        pygame.display.flip()
        clock.tick(FPS)


while True:
    start_screen()
