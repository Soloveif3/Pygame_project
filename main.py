from os import close

import pygame
import os
import sys
import random

from pygame import K_RIGHT, KSCAN_D, KSCAN_S, K_LEFT, KSCAN_A, K_UP
from pygame.examples.aliens import Player
from pygame.newbuffer import PyBUF_ND
from pygame.transform import scale

particles_group = pygame.sprite.Group()
decorative_fon = pygame.sprite.Group()

entity_group = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
hitboxes_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()

level_select_sprites = pygame.sprite.Group()
menu_sprites = pygame.sprite.Group()
pause_buttons = pygame.sprite.Group()

size = width, height = 1500, 1000
screen_rect = (0, 0, width, height)
screen = pygame.display.set_mode(size)
FPS = 30
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
            elif level[y][x] == 'G':
                Gribocheck('grib', x, y)
            elif level[y][x] == '@':
                new_player = Player(player_group, x * tile_width, y * tile_height)
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
    'lucky': load_image('sprites/interviev/Lucky_block.png'),
    'brick_undest': load_image('sprites/interviev/brick_undest.png')
}

entity_images = {
    'grib': load_image('sprites/interviev/gribocheck.png'),
    'life': load_image('sprites/interviev/life.png')
}

tile_width = tile_height = 50


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
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(entity_group, all_sprites)
        im = pygame.transform.scale(entity_images[tile_type], (tile_height, tile_width))

        self.sounds = [pygame.mixer.Sound('data/sounds/mario_jump.mp3'),
                       pygame.mixer.Sound('data/sounds/cinder_block_impact_01.mp3')]
        self.image = im

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
        if self.tile_type == 'life':
            entity_group.remove(self)
            return 1, 100, 0
        if self.tile_type == 'grib':
            return -1, -50, 3000

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
        if self.player_vel_y < 10 and self.player_jump:
            self.player_vel_y += 1
        if pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group):
            self.diference = pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group)(self.rect.bottomleft[1], 'y')
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


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tiles_group, all_sprites)
        im = pygame.transform.scale(tile_images[tile_type], (tile_height, tile_width))

        self.sounds = [pygame.mixer.Sound('data/sounds/mario_jump.mp3'),
                       pygame.mixer.Sound('data/sounds/cinder_block_impact_01.mp3')]
        self.image = im
        self.pos_in_level_x = pos_x
        self.pos_in_level_y = pos_y
        self.x_normal = pos_x * tile_width
        self.y_normal = pos_y * tile_height
        self.rect = self.image.get_rect().move(
            self.x_normal, self.y_normal)
        self.tile_type = tile_type
        self.y_vel = 0
        self.anim_going = False

    def give_random(self):
        self.jump_anim()

    def jump_anim(self):
        self.y_vel = -3
        self.anim_going = True

    def destroy_anim(self):
        create_particles(self.rect.center)
        self.sounds[1].play()

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


class Gribocheck(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(entity_group, all_sprites)
        im = pygame.transform.scale(entity_images[tile_type], (tile_height, tile_width))

        self.sounds = [pygame.mixer.Sound('data/sounds/mario_jump.mp3'),
                       pygame.mixer.Sound('data/sounds/cinder_block_impact_01.mp3')]
        self.image = im

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
        if self.tile_type == 'life':
            entity_group.remove(self)
            return 1, 100
        if self.tile_type == 'grib':
            return -1, -50

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
        if self.player_vel_y < 10 and self.player_jump:
            self.player_vel_y += 1
        if pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group):
            self.diference = pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group)(self.rect.bottomleft[1], 'y')
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


class Hitbox(pygame.sprite.Sprite):
    def __init__(self, group, pos_x, pos_y, width, height):
        super().__init__(group, all_sprites)
        self.rect = pygame.rect.Rect(pos_x, pos_y, width, height)
        self.image = pygame.Surface((width, height))


class Player(pygame.sprite.Sprite):
    def __init__(self, group, pos_x, pos_y):
        super().__init__(group, all_sprites)
        self.sounds = [pygame.mixer.Sound('data/sounds/mario_jump.mp3'),
                       pygame.mixer.Sound('data/sounds/cinder_block_impact_01.mp3')]
        self.frame_time = 0
        self.frames = []
        self.cut_frames()
        self.cur_frame = 0

        # очки и жизни
        self.score = 0
        self.lives = 1

        # уязвим ли игрок сейчас
        self.invisibility = False
        self.invisibility_time = 0

        # параметры движения
        self.touch_floor = False
        self.diference = 0
        self.player_speed = 0
        self.player_vel_y = 0
        self.player_jump = False

        self.height = 0
        self.width = 0
        self.rotation = 1
        self.image = self.frames[-2]
        self.image.set_colorkey((255, 255, 255))

        self.rect = pygame.rect.Rect(pos_x, pos_y, tile_width, tile_height)
        self.make_hitboxes()

    def make_hitboxes(self):
        self.left_hitbox = Hitbox(hitboxes_group, 0, 0, 2, tile_height - 13)
        self.right_hitbox = Hitbox(hitboxes_group, 0, 0, 2, tile_height - 13)
        self.head_hitbox = Hitbox(hitboxes_group, 0, 0, tile_width - 10, 1)
        self.leg_hitbox = Hitbox(hitboxes_group, 0, 0, tile_width - 10, 1)
        self.full_hitboxes = [self.left_hitbox, self.right_hitbox, self.leg_hitbox, self.head_hitbox]

    def cut_frames(self):  # вырезка картинок для анимаций
        self.frames.append(pygame.transform.scale(load_image('sprites/mario/injump.png'), (tile_width, tile_height)))
        self.frames.append(pygame.transform.scale(load_image('sprites/mario/lose.png'), (tile_width, tile_height)))
        self.frames.append(pygame.transform.scale(load_image('sprites/mario/run_1.png'), (tile_width, tile_height)))
        self.frames.append(pygame.transform.scale(load_image('sprites/mario/run_2.png'), (tile_width, tile_height)))
        self.frames.append(pygame.transform.scale(load_image('sprites/mario/stay.png'), (tile_width, tile_height)))
        self.frames.append(pygame.transform.scale(load_image('sprites/mario/turn.png'), (tile_width, tile_height)))

    def update(self, keys=None):
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
            self.diference = pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group)(self.rect.bottomleft[1], 'y')
            self.rect.y -= self.diference
            self.player_vel_y = 0
            self.player_jump = False
        else:
            self.player_jump = True
            self.touch_floor = False
        if pygame.sprite.spritecollideany(self, entity_group):
            do = pygame.sprite.spritecollideany(self, entity_group)[self.score]

            if do[0] < 0:
                if not self.invisibility:
                    self.lives += do[0]
                    self.invisibility_time = 250
                    self.score += do[1]
            else:
                self.lives += do[0]
                self.score += do[1]

        if self.invisibility_time <= 0:
            self.invisibility = False
        else:
            self.invisibility = True
        self.invisibility_time -= 3
        self.hitbox_move()
        # если игрок(жмет кнопки) не идет, то он замедляется
        if not (keys[K_RIGHT] or keys[K_LEFT]):
            if self.player_speed > 0:
                self.player_speed -= 1
            elif self.player_speed < 0:
                self.player_speed += 1
        self.walls()
        print(self.player_jump)
        print(self.player_vel_y)
        # смещение после всех проверок
        self.rect.x += self.player_speed
        self.rect.y += self.player_vel_y
        self.hitbox_move()
        self.anim(keys)  # анимация (смена фреима)

    def get_stats(self):
        return self.lives, self.score

    def anim(self, keys):
        if self.player_jump:
            self.image = self.frames[0]
        elif (keys[K_RIGHT] and self.player_speed < 0) or keys[K_LEFT] and self.player_speed > 0:
            self.image = self.frames[-1]
        elif self.player_speed > 2:
            self.image = self.frames[2]
        else:
            self.image = self.frames[-2]

    def hitbox_move(self):
        self.right_hitbox.rect.x = self.rect.bottomright[0]
        self.right_hitbox.rect.y = self.rect.y + 6

        self.left_hitbox.rect.x = self.rect.x - 1
        self.left_hitbox.rect.y = self.rect.y + 6

        self.leg_hitbox.rect.x = self.rect.x + 5
        self.leg_hitbox.rect.y = self.rect.bottomleft[1]

        self.head_hitbox.rect.x = self.rect.x + 5
        self.head_hitbox.rect.y = self.rect.y

    def floor(self):
        if pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group):
            self.diference = pygame.sprite.spritecollideany(self.leg_hitbox, tiles_group)(self.rect.bottomleft[1], 'y')
            self.rect.y -= self.diference + 0.2
            self.player_vel_y = 0
            self.player_jump = False
        else:
            self.player_jump = True

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
        if not self.player_jump:
            self.player_vel_y -= 15
            self.rect.y -= 2
            self.player_jump = True
            self.sounds[0].play()
        self.hitbox_move()


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
    pygame.init()
    fon = pygame.transform.scale(load_image('sprites/interface/menu_fon.jpg'), (width, height))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50

    start = Button(menu_sprites, 'sprites/interface/Play.png', 'sprites/interface/Button_fon.png', main_game,
                   width // 2 - 50,
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


def draw_groups(screen, args):
    particles_group.draw(screen)
    player_group.draw(screen)
    tiles_group.draw(screen)
    hitboxes_group.draw(screen)
    entity_group.draw(screen)
    for i in range(0, len(args), 2):
        draw_text(screen, args[i], args[i + 1], i * 200 + 100, 50, 40, 40)


def main_game():
    pygame.init()
    running = True
    a = load_level('1_level.txt')
    pl, x, y = generate_level(a)

    camera = Camera()

    # загружаем звуки
    pygame.mixer.music.load('data/sounds/super-mario-saundtrek.mp3')
    pygame.mixer.music.play(-1)
    # mario_jump_sound = pygame.mixer.Sound('data/sounds/mario_jump.mp3')  # прыжок
    # destroying_sound = pygame.mixer.Sound('data/sounds/cinder_block_impact_01.mp3')  # разрушение
    # sounds = [mario_jump_sound, destroying_sound]

    while running:
        screen.fill((92, 148, 252, 0))
        keys = pygame.key.get_pressed()
        if keys[K_RIGHT]:
            pl.move_right()
        elif keys[K_LEFT]:
            pl.move_left()
        if keys[pygame.K_SPACE] or keys[K_UP]:
            pl.jump()
        if pl.rect.y > height:
            player_group.empty()
            tiles_group.empty()
            hitboxes_group.empty()

        camera.update(pl)
        for sprite in all_sprites:
            camera.apply(sprite)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                player_group.empty()
                tiles_group.empty()
                hitboxes_group.empty()
                pygame.mixer.music.stop()

        tiles_group.update()
        player_group.update(keys)
        entity_group.update()
        particles_group.update()

        l_s = pl.get_stats()
        if not l_s[0]:
            terminate()
        draw_groups(screen, ('Score', l_s[1], 'lives', l_s[0]))

        pygame.display.flip()
        clock.tick(FPS)


start_screen()