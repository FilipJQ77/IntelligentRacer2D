import math

import pygame

MOUSE_BUTTON_LEFT = 1
COLOR_RED = pygame.color.Color(255, 0, 0)
COLOR_BLUE = pygame.color.Color(0, 0, 255)


class Create:
    def __init__(self, window: pygame.display, track_image: pygame.image):
        self.window = window
        self.track_image = track_image
        self.creating_checkpoints = True
        self.showing_checkpoints = True
        self.checkpoints = []
        self.new_checkpoint_left_point = None
        self.start_position = (0, 0)
        self.start_angle = 0

    def draw(self):
        self.window.fill((12, 145, 18))  # grass background
        self.window.blit(self.track_image, (0, 0))

        ticks = pygame.time.get_ticks()

        for checkpoint in self.checkpoints:
            first_point = checkpoint[0]
            second_point = checkpoint[1]
            color = (ticks // 2) % 255
            pygame.draw.line(self.window, (color, 0, 0), first_point, second_point, 5)

        if self.creating_checkpoints:
            if self.new_checkpoint_left_point is not None:
                pygame.draw.line(self.window, COLOR_RED, self.new_checkpoint_left_point, pygame.mouse.get_pos(), 5)

        else:  # creating start
            first_point = self.start_position
            second_point = (self.start_position[0], self.start_position[1] + 20)
            vector = (second_point[0] - first_point[0], second_point[1] - first_point[1])
            new_vector = pygame.math.Vector2.rotate(pygame.math.Vector2(vector), self.start_angle)
            second_point = (first_point[0] + new_vector.x, first_point[1] + new_vector.y)
            pygame.draw.circle(self.window, COLOR_BLUE, first_point, 5)
            pygame.draw.line(self.window, COLOR_BLUE, first_point, second_point, 5)

        pygame.display.update()

    def handle_events(self):
        stop = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop = True
                break

            keys = pygame.key.get_pressed()

            if keys[pygame.K_ESCAPE]:
                stop = True
                break

            if keys[pygame.K_z] and self.creating_checkpoints:
                self.checkpoints.pop()

            if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                ctrl = True
            else:
                ctrl = False

            if self.creating_checkpoints:
                self.create_checkpoint(event)
                if ctrl:
                    self.creating_checkpoints = False
            else:
                self.create_start_position(event)
                if ctrl:
                    stop = True

            if ctrl and keys[pygame.K_c]:
                self.showing_checkpoints = not self.showing_checkpoints

        return stop

    def create_checkpoint(self, event: pygame.event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_BUTTON_LEFT:
            self.new_checkpoint_left_point = pygame.mouse.get_pos()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == MOUSE_BUTTON_LEFT:
            self.checkpoints.append((self.new_checkpoint_left_point, pygame.mouse.get_pos()))
            self.new_checkpoint_left_point = None

    def create_start_position(self, event: pygame.event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_BUTTON_LEFT:
            self.start_position = pygame.mouse.get_pos()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == MOUSE_BUTTON_LEFT:
            point1 = self.start_position
            point2 = pygame.mouse.get_pos()
            # if the x coordinates are the same, we cant divide by zero
            if point1[0] == point2[0]:
                self.start_angle = 0
            else:
                self.start_angle = math.degrees(math.atan2(point2[1] - point1[1], point2[0] - point1[0])) - 90
