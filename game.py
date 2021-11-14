from abc import ABC
from collections import namedtuple
from utilities import rotate_image, scale_image, get_human_player_input
import math
import pygame

CAR = scale_image(pygame.image.load("img/purple-car.png"), 0.6)
CAR_WIDTH = CAR.get_width()
CAR_HEIGHT = CAR.get_height()
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


class Car(ABC):
    def __init__(self, acceleration, deceleration, brake_power, max_velocity, rotation_speed, start_angle=0,
                 start_position=(0, 0)):
        self.acceleration = acceleration
        self.brake_power = brake_power
        self.deceleration = deceleration
        self.max_velocity = max_velocity
        self.velocity = 0
        self.rotation_speed = rotation_speed
        self.angle = start_angle
        self.x, self.y = start_position
        self.image = CAR
        self.image_rect = self.image.get_rect()

    def rotate(self, left=False, right=False):
        if self.velocity > 0:
            if left:
                self.angle += self.rotation_speed
            elif right:
                self.angle -= self.rotation_speed

    def accelerate(self):
        self.velocity = min(self.velocity + self.acceleration, self.max_velocity)

    def decelerate(self):
        self.velocity = max(self.velocity - self.deceleration, 0)

    def brake(self):
        self.velocity = max(self.velocity - self.brake_power, 0)

    def collide(self, mask, x, y):
        car_mask = pygame.mask.from_surface(self.image)
        offset_x, offset_y, _, _ = self.image_rect
        offset = (offset_x, offset_y)
        intersection_point = mask.overlap(car_mask, offset)
        return intersection_point

    def bounce(self):
        # self.velocity = -self.velocity  # todo improve
        print(f"Collide {pygame.time.get_ticks()}")

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

        # get current car position with rotation
        self.image, self.image_rect = rotate_image(CAR, (self.x, self.y), (CAR_WIDTH / 2, CAR_HEIGHT / 2), self.angle)

        if self.collide(TRACK_BORDER_MASK, 0, 0):
            self.bounce()

    def draw(self, window):
        window.blit(self.image, self.image_rect)
        pygame.draw.circle(window, (255, 0, 0), (self.x, self.y), 5)


class Game:
    def __init__(self):
        self.car_acceleration = 0.7
        self.car_deceleration = 0.2
        self.car_brake_power = 0.5
        self.car_max_velocity = 10
        self.car_rotation_velocity = 3.7
        self.car_start_angle = 180
        self.car_start_position = (100, 0)

    def initialise_car(self):
        return Car(self.car_acceleration,
                   self.car_deceleration,
                   self.car_brake_power,
                   self.car_max_velocity,
                   self.car_rotation_velocity,
                   self.car_start_angle,
                   self.car_start_position)

    def draw(self, window, images, car):
        window.fill((12, 145, 18))

        for image, position in images:
            window.blit(image, position)

        car.draw(window)
        pygame.display.update()

    def human_player_game_loop(self):
        running = True
        clock = pygame.time.Clock()

        player = self.initialise_car()

        images = [(TRACK, (0, 0))]

        while running:
            clock.tick(FPS)

            self.draw(WINDOW, images, player)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

            action = get_human_player_input()

            player.move_player(action)

        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.human_player_game_loop()
