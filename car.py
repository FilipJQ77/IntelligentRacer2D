import math
from collections import namedtuple

import pygame

from utilities import rotate_image, distance_from_point_and_line


class CarSpecification:
    def __init__(self, acceleration, deceleration, brake_power, max_speed, max_angle):
        self.acceleration = acceleration
        self.brake_power = brake_power
        self.deceleration = deceleration
        self.max_speed = max_speed
        self.max_angle = max_angle


class Car:
    def __init__(self, car_specification: CarSpecification, car_image, start_angle=0, start_position=(0, 0)):
        self.acceleration = car_specification.acceleration
        self.brake_power = car_specification.brake_power
        self.deceleration = car_specification.deceleration
        self.max_speed = car_specification.max_speed
        self.max_angle = car_specification.max_angle
        self.speed = 0
        self.angle = start_angle
        self.x, self.y = start_position
        self.original_image = self.image = car_image
        self.width, self.height = car_image.get_width(), car_image.get_height()

        self.image_rect = self.image.get_rect()

    def rotate(self, left=False, right=False):
        # the faster you go, the less you can steer
        angle = (-self.max_angle * self.speed) / (4 * self.max_speed) + self.max_angle
        # angle = (-self.max_angle * self.speed) / (2 * self.max_speed) + self.max_angle
        if left:
            self.angle += angle
        elif right:
            self.angle -= angle

    def accelerate(self):
        self.speed = min(self.speed + self.acceleration, self.max_speed)

    def decelerate(self):
        self.speed = max(self.speed - self.deceleration, 0)

    def brake(self):
        self.speed = max(self.speed - self.brake_power, 0)

    def collide(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.image)
        offset_x, offset_y, _, _ = self.image_rect
        offset = (offset_x - x, offset_y - y)
        intersection_point = mask.overlap(car_mask, offset)
        return intersection_point

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
        self.image, self.image_rect = rotate_image(self.original_image, (self.x, self.y),
                                                   (self.width / 2, self.height / 2), self.angle)

    def get_distance_from_checkpoint(self, checkpoint):
        return distance_from_point_and_line(checkpoint[0], checkpoint[1], (self.x, self.y))

    def check_checkpoint_pass(self, distance):
        if distance < self.width:
            return True
        else:
            return False

    def draw(self, window):
        window.blit(self.image, self.image_rect)
        # pygame.draw.circle(window, (255, 0, 0), (self.x, self.y), 5)
