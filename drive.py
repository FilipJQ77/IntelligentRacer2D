import pygame

from car import Car

MOUSE_BUTTON_LEFT = 1
COLOR_RED = pygame.color.Color(255, 0, 0)
COLOR_BLUE = pygame.color.Color(0, 0, 255)


class Drive:
    def __init__(self, window: pygame.display, track_image: pygame.image, track_border_image: pygame.image, car_image,
                 start_position, start_angle, checkpoints,
                 fps):
        self.window = window
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = fps

        self.car_image = car_image
        self.track = track_image
        self.track_border = track_border_image
        self.track_border_mask = pygame.mask.from_surface(self.track_border)
        self.track_width = track_image.get_width()
        self.track_height = track_image.get_height()

        self.car_acceleration = 0.7
        self.car_deceleration = 0.2
        self.car_brake_power = 0.5
        self.car_max_speed = 10
        self.car_max_angle = 6

        self.start_angle = start_angle
        self.start_position = start_position
        self.player_car = self.initialise_car()

        self.images = [(self.track, (0, 0))]
        self.checkpoints = checkpoints
        self.new_checkpoint_left_point = None
        self.checkpoint_counter = 0

        self.creating_start = True
        self.creating_checkpoints = True
        self.showing_checkpoints = True

    def initialise_car(self):
        return Car(self.car_acceleration,
                   self.car_deceleration,
                   self.car_brake_power,
                   self.car_max_speed,
                   self.car_max_angle,
                   self.car_image,
                   self.start_angle,
                   self.start_position)

    def get_distance_from_checkpoint(self):
        return self.player_car.get_distance_from_checkpoint(
            self.checkpoints[self.checkpoint_counter % len(self.checkpoints)])

    def draw(self):
        self.window.fill((12, 145, 18))

        for image, position in self.images:
            self.window.blit(image, position)

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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                break

            keys = pygame.key.get_pressed()

            if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                ctrl = True
            else:
                ctrl = False

            if ctrl and keys[pygame.K_c]:
                self.showing_checkpoints = not self.showing_checkpoints

            if keys[pygame.K_ESCAPE]:
                stop = True

        return stop

    def restart(self):
        self.player_car = self.initialise_car()
        self.checkpoint_counter = 0

    def step(self, action) -> (bool, bool):
        self.clock.tick(self.fps)
        self.draw()
        stop = self.handle_events()

        game_over = False

        self.player_car.move_player(action)

        checkpoint_passed = self.player_car.check_checkpoint_pass(self.get_distance_from_checkpoint())
        if checkpoint_passed:
            self.checkpoint_counter += 1

        if self.player_car.collide(self.track_border_mask):
            game_over = True

        return game_over, stop


if __name__ == '__main__':
    game = Drive()
    game.game_loop()
