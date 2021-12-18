from abc import ABC
from collections import namedtuple

import utilities
from utilities import distance_from_point_and_line, rotate_image, scale_image, get_human_player_input
import json
import math
import pygame

CAR = scale_image(pygame.image.load("img/purple-car.png"), 0.6)
CAR_WIDTH = CAR.get_width()
CAR_HEIGHT = CAR.get_height()
TRACK = pygame.image.load("img/track.png")
TRACK_BORDER = pygame.image.load("img/track_border.png")
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)
pygame.display.set_caption("Racer 2D")

FPS = 60
WIDTH = TRACK.get_width()
HEIGHT = TRACK.get_height()
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))

MOUSE_BUTTON_LEFT = 1
COLOR_RED = pygame.color.Color(255, 0, 0)


class Car(ABC):
    def __init__(self, acceleration, deceleration, brake_power, max_speed, max_rotation_speed, start_angle=0,
                 start_position=(0, 0)):
        self.acceleration = acceleration
        self.brake_power = brake_power
        self.deceleration = deceleration
        self.speed = 0
        self.max_speed = max_speed
        self.max_rotation_speed = max_rotation_speed
        self.angle = start_angle
        self.x, self.y = start_position
        self.image = CAR
        self.image_rect = self.image.get_rect()

    def rotate(self, left=False, right=False):
        if self.speed > 0:
            # the faster you go, the less you can steer
            # TODO a bit more turning ability at higher speed
            rotation_speed = (-self.max_rotation_speed * self.speed) / (2 * self.max_speed) + self.max_rotation_speed
            if left:
                self.angle += rotation_speed
            elif right:
                self.angle -= rotation_speed

    def accelerate(self):
        self.speed = min(self.speed + self.acceleration, self.max_speed)

    def decelerate(self):
        self.speed = max(self.speed - self.deceleration, 0)

    def brake(self):
        self.speed = max(self.speed - self.brake_power, 0)

    def collide(self, mask, x, y):
        car_mask = pygame.mask.from_surface(self.image)
        offset_x, offset_y, _, _ = self.image_rect
        offset = (offset_x - x, offset_y - y)
        intersection_point = mask.overlap(car_mask, offset)
        return intersection_point

    def bounce(self):
        # self.velocity = -self.velocity  # todo improve
        print(f"Collide {pygame.time.get_ticks()}")

    def move(self):
        angle = math.radians(self.angle)
        vertical_velocity = math.cos(angle) * self.speed
        horizontal_velocity = math.sin(angle) * self.speed

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

        # get current car position with rotation after moving
        self.image, self.image_rect = rotate_image(CAR, (self.x, self.y), (CAR_WIDTH / 2, CAR_HEIGHT / 2), self.angle)

        if self.collide(TRACK_BORDER_MASK, 0, 0):
            self.bounce()

    def check_checkpoint_pass(self, checkpoint):
        distance = distance_from_point_and_line(checkpoint[0], checkpoint[1], (self.x, self.y))
        if distance < CAR_WIDTH:
            return True
        else:
            return False

    def draw(self, window):
        window.blit(self.image, self.image_rect)
        # pygame.draw.circle(window, (255, 0, 0), (self.x, self.y), 5)


class Game:
    def __init__(self):
        self.window = WINDOW
        self.running = True
        self.clock = pygame.time.Clock()

        self.car_acceleration = 0.7
        self.car_deceleration = 0.2
        self.car_brake_power = 0.5
        self.car_max_speed = 10
        self.car_max_rotation_speed = 6

        self.car_start_angle = 180
        self.car_start_position = (100, 0)
        self.player_car = self.initialise_car()

        self.images = [(TRACK, (0, 0))]
        self.checkpoints = []
        self.new_checkpoint_left_point = None
        self.checkpoint_index = 0
        self.creating_checkpoints = True
        self.showing_checkpoints = True

    def initialise_car(self):
        return Car(self.car_acceleration,
                   self.car_deceleration,
                   self.car_brake_power,
                   self.car_max_speed,
                   self.car_max_rotation_speed,
                   self.car_start_angle,
                   self.car_start_position)

    def draw(self):
        self.window.fill((12, 145, 18))

        for image, position in self.images:
            self.window.blit(image, position)

        ticks = pygame.time.get_ticks()

        if self.showing_checkpoints:
            if self.creating_checkpoints:
                for checkpoint in self.checkpoints:
                    first_point = checkpoint[0]
                    second_point = checkpoint[1]
                    color = (ticks // 2) % 255
                    pygame.draw.line(self.window, (color, 0, 0), first_point, second_point, 5)

                if self.new_checkpoint_left_point is not None:
                    pygame.draw.line(self.window, COLOR_RED, self.new_checkpoint_left_point, pygame.mouse.get_pos(), 5)
            else:
                # get next 3 checkpoints
                len_checkpoints = len(self.checkpoints) - 1
                current_checkpoint = self.checkpoints[self.checkpoint_index]
                next_checkpoint = self.checkpoints[(self.checkpoint_index + 1) % len_checkpoints]
                next_next_checkpoint = self.checkpoints[(self.checkpoint_index + 2) % len_checkpoints]

                # draw checkpoint lines
                pygame.draw.line(self.window, COLOR_RED, current_checkpoint[0], current_checkpoint[1], 5)
                pygame.draw.line(self.window, COLOR_RED, next_checkpoint[0], next_checkpoint[1], 5)
                pygame.draw.line(self.window, COLOR_RED, next_next_checkpoint[0], next_next_checkpoint[1], 5)

        self.player_car.draw(self.window)

        pygame.display.update()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                break

            if self.creating_checkpoints:
                self.create_new_checkpoint(event)

            keys = pygame.key.get_pressed()

            if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                ctrl = True
            else:
                ctrl = False

            if ctrl:
                if keys[pygame.K_s]:
                    self.save_checkpoints()
                elif keys[pygame.K_l]:
                    self.load_checkpoints()
                elif keys[pygame.K_c]:
                    self.showing_checkpoints = not self.showing_checkpoints

    def create_new_checkpoint(self, event: pygame.event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_BUTTON_LEFT:
            self.new_checkpoint_left_point = pygame.mouse.get_pos()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == MOUSE_BUTTON_LEFT:
            self.checkpoints.append((self.new_checkpoint_left_point, pygame.mouse.get_pos()))
            self.new_checkpoint_left_point = None

    def save_checkpoints(self):
        with open("data/track_checkpoints.json", 'w') as file:
            json.dump(self.checkpoints, file)
        self.creating_checkpoints = False
        self.showing_checkpoints = False

    def load_checkpoints(self):
        try:
            with open("data/track_checkpoints.json", 'r') as file:
                self.checkpoints = json.load(file)
            self.creating_checkpoints = False
            self.showing_checkpoints = False
        except Exception as e:
            print(e)

    def human_player_game_loop(self):
        while self.running:
            self.clock.tick(FPS)  # todo move car with delta time?

            self.draw()

            self.handle_events()

            if not self.creating_checkpoints:
                action = get_human_player_input()
                self.player_car.move_player(action)
                checkpoint_passed = self.player_car.check_checkpoint_pass(self.checkpoints[self.checkpoint_index])
                if checkpoint_passed:
                    self.checkpoint_index = (self.checkpoint_index + 1) % len(self.checkpoints)

        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.human_player_game_loop()
