import pygame
import sys

# Инициализация Pygame
pygame.init()

# Настройки экрана
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Kill Enemies by Jumping")

# Цвета
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Класс игрока
class Player:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = RED
        self.vel_y = 0
        self.jump = False

    def update(self):
        # Гравитация
        self.vel_y += 1
        self.rect.y += self.vel_y

        # Ограничение падения на землю
        if self.rect.bottom >= SCREEN_HEIGHT - 50:
            self.rect.bottom = SCREEN_HEIGHT - 50
            self.vel_y = 0
            self.jump = False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

# Класс врага
class Enemy:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = GREEN
        self.alive = True

    def draw(self, screen):
        if self.alive:
            pygame.draw.rect(screen, self.color, self.rect)


# Основной цикл игры
clock = pygame.time.Clock()
player = Player(100, 100, 50, 50)
enemies = [Enemy(400, 500, 50, 50), Enemy(600, 500, 50, 50)]  # Список врагов

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Управление игроком
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player.rect.x -= 5
    if keys[pygame.K_RIGHT]:
        player.rect.x += 5
    if keys[pygame.K_SPACE] and not player.jump:
        player.vel_y = -15
        player.jump = True

    # Обновление игрока
    player.update()

    # Проверка столкновений с врагами
    for enemy in enemies:
        if enemy.alive and player.rect.colliderect(enemy.rect):
            # Проверка, что игрок запрыгнул на врага
            if player.vel_y > 0 and player.rect.bottom <= enemy.rect.top + 10:
                enemy.alive = False  # Убиваем врага
                player.vel_y = -10  # Отскок игрока

    # Отрисовка
    screen.fill(WHITE)
    player.draw(screen)
    for enemy in enemies:
        enemy.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()