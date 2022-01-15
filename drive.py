import numpy as np
import pygame

from car import Car, CarSpecification

MOUSE_BUTTON_LEFT = 1
COLOR_RED = pygame.color.Color(255, 0, 0)


class Drive:
    def __init__(self, window: pygame.display, track_image: pygame.image, track_border_image: pygame.image, car_image,
                 car_specification: CarSpecification, checkpoints, start_position, start_angle):
        self.window = window

        self.car_image = car_image
        self.track = track_image
        self.track_border = track_border_image
        self.track_border_mask = pygame.mask.from_surface(self.track_border)
        self.track_width = track_image.get_width()
        self.track_height = track_image.get_height()

        self.car_specification = car_specification
        self.start_angle = start_angle
        self.start_position = start_position
        self.player_car = self.initialise_car()

        self.images = [(self.track, (0, 0))]
        self.checkpoints = checkpoints
        self.showing_checkpoints = True
        self.checkpoint_counter = 0

    def initialise_car(self):
        return Car(self.car_specification,
                   self.car_image,
                   self.start_angle,
                   self.start_position)

    def get_distance_from_checkpoint(self):
        return self.player_car.get_distance_from_checkpoint(
            self.checkpoints[self.checkpoint_counter % len(self.checkpoints)])

    def get_state(self):
        # next 3 checkpoints
        len_checkpoints = len(self.checkpoints)
        checkpoint_1 = self.checkpoints[self.checkpoint_counter % len_checkpoints]
        # checkpoint_2 = game.checkpoints[(game.checkpoint_counter + 1) % len_checkpoints]
        # checkpoint_3 = game.checkpoints[(game.checkpoint_counter + 2) % len_checkpoints]

        state = [
            # current car state
            self.player_car.x,
            self.player_car.y,
            self.player_car.angle,
            self.player_car.speed,

            # car specification
            # game.car_acceleration,
            # game.car_deceleration,
            # game.car_brake_power,
            # game.car_max_speed,
            # game.car_max_rotation_speed,

            checkpoint_1[0][0],  # left point x
            checkpoint_1[0][1],  # left point y
            checkpoint_1[1][0],  # right point x
            checkpoint_1[1][1],  # right point y

            # checkpoint_2[0][0],  # left point x
            # checkpoint_2[0][1],  # left point y
            # checkpoint_2[1][0],  # right point x
            # checkpoint_2[1][1],  # right point y

            # checkpoint_3[0][0],  # left point x
            # checkpoint_3[0][1],  # left point y
            # checkpoint_3[1][0],  # right point x
            # checkpoint_3[1][1],  # right point y
        ]

        return np.array(state, dtype=np.float64)

    def draw(self):
        self.window.fill((12, 145, 18))

        self.window.blit(self.track, (0, 0))

        self.player_car.draw(self.window)

        if self.showing_checkpoints:
            # get next 3 checkpoints
            len_checkpoints = len(self.checkpoints)
            current_checkpoint = self.checkpoints[self.checkpoint_counter % len_checkpoints]
            next_checkpoint = self.checkpoints[(self.checkpoint_counter + 1) % len_checkpoints]
            next_next_checkpoint = self.checkpoints[(self.checkpoint_counter + 2) % len_checkpoints]

            # draw next checkpoints lines
            pygame.draw.line(self.window, COLOR_RED, current_checkpoint[0], current_checkpoint[1], 5)
            pygame.draw.line(self.window, COLOR_RED, next_checkpoint[0], next_checkpoint[1], 5)
            pygame.draw.line(self.window, COLOR_RED, next_next_checkpoint[0], next_next_checkpoint[1], 5)

        pygame.display.update()

    def handle_events(self):
        stop = False
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
                stop = True
                break

            if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                ctrl = True
            else:
                ctrl = False

            if ctrl and keys[pygame.K_c]:
                self.showing_checkpoints = not self.showing_checkpoints

        return stop

    def restart(self):
        self.player_car = self.initialise_car()
        self.checkpoint_counter = 0

    def step(self, action) -> bool:
        game_over = False

        self.player_car.move_player(action)

        checkpoint_passed = self.player_car.check_checkpoint_pass(self.get_distance_from_checkpoint())
        if checkpoint_passed:
            self.checkpoint_counter += 1

        if self.player_car.collide(self.track_border_mask):
            game_over = True

        return game_over
