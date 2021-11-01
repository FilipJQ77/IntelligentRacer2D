from abc import ABC
import math
import pygame
import time

CAR = pygame.image.load("img/purple-car.png")
TRACK = pygame.image.load("img/track.png")
pygame.display.set_caption("Racer 2D")

FPS = 60
# WIDTH = 800
WIDTH = TRACK.get_width()
# HEIGHT = 800
HEIGHT = TRACK.get_height()
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))


def blit_rotate_center(window, image, top_left, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=top_left).center)
    window.blit(rotated_image, new_rect.topleft)


class Car(ABC):
    def __init__(self, acceleration, deceleration, brake_power, max_velocity, rotation_velocity, start_angle=0,
                 start_position=(0, 0)):
        self.image = CAR
        self.acceleration = acceleration
        self.brake_power = brake_power
        self.deceleration = deceleration
        self.max_speed = max_velocity
        self.velocity = 0
        self.rotation_speed = rotation_velocity
        self.angle = start_angle
        self.x, self.y = start_position

    def rotate(self, left=False, right=False):
        if self.velocity > 0:
            if left:
                self.angle += self.rotation_speed
            elif right:
                self.angle -= self.rotation_speed

    def accelerate(self):
        self.velocity = min(self.velocity + self.acceleration, self.max_speed)

    def decelerate(self):
        self.velocity = max(self.velocity - self.deceleration, 0)

    def brake(self):
        self.velocity = max(self.velocity - self.brake_power, 0)

    def move(self):
        angle = math.radians(self.angle)
        vertical_velocity = math.cos(angle) * self.velocity
        horizontal_velocity = math.sin(angle) * self.velocity

        self.x -= horizontal_velocity
        self.y -= vertical_velocity

    def draw(self, window):
        blit_rotate_center(window, self.image, (self.x, self.y), self.angle)


def draw(window, images, car):
    window.fill((255, 255, 255))

    for image, position in images:
        window.blit(image, position)

    car.draw(window)
    pygame.display.update()


def main():
    running = True
    clock = pygame.time.Clock()

    acceleration = 0.5
    deceleration = 0.1
    brake_power = 0.5
    max_velocity = 10
    rotation_velocity = 4
    start_angle = 180
    start_position = (100, 0)
    player = Car(acceleration, deceleration, brake_power, max_velocity, rotation_velocity, start_angle, start_position)

    images = [(TRACK, (0, 0))]

    while running:
        clock.tick(FPS)

        draw(WINDOW, images, player)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.rotate(left=True)
        if keys[pygame.K_RIGHT]:
            player.rotate(right=True)
        if not keys[pygame.K_UP] and not keys[pygame.K_DOWN]:
            player.decelerate()
        else:
            if keys[pygame.K_UP]:
                player.accelerate()
            if keys[pygame.K_DOWN]:
                player.brake()
        player.move()

    pygame.quit()


if __name__ == '__main__':
    main()
