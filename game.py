from abc import ABC
from collections import namedtuple
from utilities import blit_rotate_center, scale_image, key_left, key_right, key_up, key_down
import math
import pygame
import time

CAR = scale_image(pygame.image.load("img/purple-car.png"), 0.6)
TRACK = pygame.image.load("img/track.png")
# TRACK = pygame.image.load("img/track2.png")
TRACK_BORDER = pygame.image.load("img/track_border.png")
# TRACK_BORDER = pygame.image.load("img/track2_border.png")
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)
pygame.display.set_caption("Racer 2D")

FPS = 60
# WIDTH = 800
WIDTH = TRACK.get_width()
# HEIGHT = 800
HEIGHT = TRACK.get_height()
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))

DEBUG = False


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

    def collide(self, mask, x, y):
        rotated_car = pygame.transform.rotate(CAR, self.angle)
        car_mask = pygame.mask.from_surface(rotated_car)
        offset = (int(self.x - x), int(self.y - y))
        intersection_point = mask.overlap(car_mask, offset)
        return intersection_point

    def bounce(self):
        # self.velocity = -self.velocity  # todo improve
        print(f"Collide {pygame.time.get_ticks()} {DEBUG}")

    def move(self):
        angle = math.radians(self.angle)
        vertical_velocity = math.cos(angle) * self.velocity
        horizontal_velocity = math.sin(angle) * self.velocity

        self.x -= horizontal_velocity
        self.y -= vertical_velocity

    def move_player(self, action: namedtuple):
        if action.left:
            self.rotate(left=True)
        if action.right:
            self.rotate(right=True)
        if not action.throttle and not action.brake:
            self.decelerate()
        else:
            if action.throttle:
                self.accelerate()
            if action.brake:
                self.brake()

        self.move()

        if self.collide(TRACK_BORDER_MASK, 0, 0):
            self.bounce()

    def draw(self, window):
        rotated_car = pygame.transform.rotate(CAR, self.angle)
        offset = (int(self.x), int(self.y))
        car_mask = pygame.mask.from_surface(rotated_car)

        # todo remove
        if DEBUG:
            window.blit(rotated_car, offset)
        else:
            blit_rotate_center(window, self.image, (self.x, self.y), self.angle)
            
        pygame.draw.circle(window, (255, 0, 0), (self.x, self.y), 5)


def draw(window, images, car):
    window.fill((12, 145, 18))

    for image, position in images:
        window.blit(image, position)

    car.draw(window)
    pygame.display.update()


def main():
    running = True
    clock = pygame.time.Clock()

    acceleration = 0.3
    deceleration = 0.1
    brake_power = 0.5
    max_velocity = 6
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
        # todo remove
        global DEBUG
        if keys[pygame.K_t]:
            DEBUG = not DEBUG

        action = namedtuple("Action", ("throttle", "brake", "left", "right"))

        if key_up(keys):
            action.throttle = True
        else:
            action.throttle = False

        if key_down(keys):
            action.brake = True
        else:
            action.brake = False

        if key_left(keys):
            action.left = True
        else:
            action.left = False

        if key_right(keys):
            action.right = True
        else:
            action.right = False

        player.move_player(action)

    pygame.quit()


if __name__ == '__main__':
    main()
