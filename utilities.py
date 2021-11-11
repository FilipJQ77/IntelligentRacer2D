import pygame


def scale_image(image, factor):
    size = round(image.get_width() * factor), round(image.get_height() * factor)
    return pygame.transform.scale(image, size)


# https://stackoverflow.com/a/54714144
def rotate_image(image, position, origin_position, angle):
    # offset from pivot to center
    image_rect = image.get_rect(topleft=(position[0] - origin_position[0], position[1] - origin_position[1]))
    offset_center_to_pivot = pygame.math.Vector2(position) - image_rect.center

    # roatated offset from pivot to center
    rotated_offset = offset_center_to_pivot.rotate(-angle)

    # roatetd image center
    rotated_image_center = (position[0] - rotated_offset.x, position[1] - rotated_offset.y)

    # get a rotated image
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_image_rect = rotated_image.get_rect(center=rotated_image_center)

    return rotated_image, rotated_image_rect


def key_left(keys) -> bool:
    return keys[pygame.K_LEFT] or keys[pygame.K_a]


def key_right(keys) -> bool:
    return keys[pygame.K_RIGHT] or keys[pygame.K_d]


def key_up(keys) -> bool:
    return keys[pygame.K_UP] or keys[pygame.K_w]


def key_down(keys) -> bool:
    return keys[pygame.K_DOWN] or keys[pygame.K_s] or keys[pygame.K_SPACE]
