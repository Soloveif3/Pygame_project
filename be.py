import pygame
import sys

# Инициализация pygame
pygame.init()

# Настройки экрана
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simple Mario-like Game")

# Цвета
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Настройки персонажа
player_width = 40
player_height = 60
player_x = 50
player_y = SCREEN_HEIGHT - player_height - 50
player_vel_y = 0
player_jump = False

# Настройки платформы
platform_width = 200
platform_height = 20
platform_x = 300
platform_y = SCREEN_HEIGHT - 150

# Основной цикл игры
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Управление персонажем
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_x -= 5
    if keys[pygame.K_RIGHT]:
        player_x += 5
    if keys[pygame.K_SPACE] and not player_jump:
        player_vel_y = -15
        player_jump = True

    # Гравитация
    player_vel_y += 1
    player_y += player_vel_y

    # Проверка столкновения с платформой
    if player_y + player_height >= platform_y and player_x + player_width >= platform_x and player_x <= platform_x + platform_width:
        player_y = platform_y - player_height
        player_vel_y = 0
        player_jump = False

    # Проверка столкновения с землей
    if player_y + player_height >= SCREEN_HEIGHT - 50:
        player_y = SCREEN_HEIGHT - player_height - 50
        player_vel_y = 0
        player_jump = False

    # Отрисовка
    screen.fill(WHITE)
    pygame.draw.rect(screen, BLUE, (player_x, player_y, player_width, player_height))
    pygame.draw.rect(screen, GREEN, (platform_x, platform_y, platform_width, platform_height))

    # Обновление экрана
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()