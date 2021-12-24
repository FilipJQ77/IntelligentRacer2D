from collections import namedtuple
import numpy as np
import numpy.linalg as linalg
import pygame


def scale_image(image, factor):
    size = round(image.get_width() * factor), round(image.get_height() * factor)
    return pygame.transform.scale(image, size)


# https://stackoverflow.com/a/54714144
def rotate_image(image, position, origin_position, angle):
    """
    :param image:
    :param position:
    :param origin_position:
    :param angle: angle in degrees
    :return:
    """
    # offset from pivot to center
    image_rect = image.get_rect(topleft=(position[0] - origin_position[0], position[1] - origin_position[1]))
    offset_center_to_pivot = pygame.math.Vector2(position) - image_rect.center

    # rotated offset from pivot to center
    rotated_offset = offset_center_to_pivot.rotate(-angle)

    # rotated image center
    rotated_image_center = (position[0] - rotated_offset.x, position[1] - rotated_offset.y)

    # get a rotated image
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_image_rect = rotated_image.get_rect(center=rotated_image_center)

    return rotated_image, rotated_image_rect


def distance_from_point_and_line(p1, p2, p3):
    """
    p1, p2 - line points
    p3 - point
    """
    p1 = np.asarray(p1)
    p2 = np.asarray(p2)
    p3 = np.asarray(p3)
    return linalg.norm(np.cross(p2 - p1, p1 - p3)) / linalg.norm(p2 - p1)


def create_action_tuple():
    return namedtuple("Action", ("throttle", "brake", "left", "right"))


def choose_action(index: int):
    """
    0 - nothing
    1 - throttle
    2 - brake
    3 - left
    4 - right
    5 - throttle + brake
    6 - throttle + left
    7 - throttle + right
    8 - brake + left
    9 - brake + right
    10 - throttle + brake + left
    11 - throttle + brake + right
    There are no left + right because it does not make sense to steer in both directions.
    :param index: action index
    :return: action
    """
    action = create_action_tuple()
    throttle = 0
    brake = 0
    left = 0
    right = 0
    if index == 1:
        throttle = 1
    elif index == 2:
        brake = 1
    elif index == 3:
        left = 1
    elif index == 4:
        right = 1
    elif index == 5:
        throttle = 1
        brake = 1
    elif index == 6:
        throttle = 1
        left = 1
    elif index == 7:
        throttle = 1
        right = 1
    elif index == 8:
        brake = 1
        left = 1
    elif index == 9:
        brake = 1
        right = 1
    elif index == 10:
        throttle = 1
        brake = 1
        left = 1
    elif index == 11:
        throttle = 1
        brake = 1
        right = 1

    action.throttle = throttle
    action.brake = brake
    action.left = left
    action.right = right
    return action


def key_left(keys) -> bool:
    return keys[pygame.K_LEFT] or keys[pygame.K_a]


def key_right(keys) -> bool:
    return keys[pygame.K_RIGHT] or keys[pygame.K_d]


def key_up(keys) -> bool:
    return keys[pygame.K_UP] or keys[pygame.K_w]


def key_down(keys) -> bool:
    return keys[pygame.K_DOWN] or keys[pygame.K_s] or keys[pygame.K_SPACE]


def get_human_player_input():
    action = create_action_tuple()
    keys = pygame.key.get_pressed()

    if key_up(keys):
        action.throttle = 1
    else:
        action.throttle = 0
    if key_down(keys):
        action.brake = 1
    else:
        action.brake = 0
    if key_left(keys):
        action.left = 1
    else:
        action.left = 0
    if key_right(keys):
        action.right = 1
    else:
        action.right = 0

    return action
