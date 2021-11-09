import pygame


def scale_image(image, factor):
    size = round(image.get_width() * factor), round(image.get_height() * factor)
    return pygame.transform.scale(image, size)


def blit_rotate_center(window, image, top_left, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=top_left).center)
    window.blit(rotated_image, new_rect.topleft)


def key_left(keys) -> bool:
    return keys[pygame.K_LEFT] or keys[pygame.K_a]


def key_right(keys) -> bool:
    return keys[pygame.K_RIGHT] or keys[pygame.K_d]


def key_up(keys) -> bool:
    return keys[pygame.K_UP] or keys[pygame.K_w]


def key_down(keys) -> bool:
    return keys[pygame.K_DOWN] or keys[pygame.K_s] or keys[pygame.K_SPACE]
