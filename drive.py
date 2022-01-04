import json
import math
import pygame

from car import Car
from utilities import get_human_player_input

MOUSE_BUTTON_LEFT = 1
COLOR_RED = pygame.color.Color(255, 0, 0)
COLOR_BLUE = pygame.color.Color(0, 0, 255)


class Drive:
    def __init__(self, window: pygame.display, track_image: pygame.image, track_border_image: pygame.image):
        self.window = window
        self.running = True
        self.clock = pygame.time.Clock()

        self.track = track_image
        self.track_border = track_border_image
        self.self.track_border_mask = pygame.mask.from_surface(self.track_border)
        self.track_width = track_image.get_width()
        self.track_height = track_image.get_height()

        self.car_acceleration = 0.7
        self.car_deceleration = 0.2
        self.car_brake_power = 0.5
        self.car_max_speed = 10
        self.car_max_angle = 6

        self.start_angle = 0
        self.start_position = (0, 0)
        self.player_car = self.initialise_car()

        self.images = [(self.track, (0, 0))]
        self.checkpoints = []
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
                   self.start_angle,
                   self.start_position)

    def get_distance_from_checkpoint(self):
        return self.player_car.get_distance_from_checkpoint(
            self.checkpoints[self.checkpoint_counter % len(self.checkpoints)])

    def draw(self):
        self.window.fill((12, 145, 18))

        for image, position in self.images:
            self.window.blit(image, position)

        ticks = pygame.time.get_ticks()

        if self.creating_checkpoints:
            for checkpoint in self.checkpoints:
                first_point = checkpoint[0]
                second_point = checkpoint[1]
                color = (ticks // 2) % 255
                pygame.draw.line(self.window, (color, 0, 0), first_point, second_point, 5)

            if self.new_checkpoint_left_point is not None:
                pygame.draw.line(self.window, COLOR_RED, self.new_checkpoint_left_point, pygame.mouse.get_pos(), 5)

        elif self.creating_start:
            first_point = self.start_position
            second_point = (self.start_position[0], self.start_position[1] + 20)
            vector = (second_point[0] - first_point[0], second_point[1] - first_point[1])
            new_vector = pygame.math.Vector2.rotate(pygame.math.Vector2(vector), self.start_angle)
            second_point = (first_point[0] + new_vector.x, first_point[1] + new_vector.y)
            pygame.draw.circle(self.window, COLOR_BLUE, first_point, 5)
            pygame.draw.line(self.window, COLOR_BLUE, first_point, second_point, 5)

        else:
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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                break

            keys = pygame.key.get_pressed()

            if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                ctrl = True
            else:
                ctrl = False

            if self.creating_checkpoints:
                self.create_checkpoint(event)
                if ctrl:
                    checkpoints_done = False
                    if keys[pygame.K_s]:
                        self.save_checkpoints()
                        checkpoints_done = True
                    elif keys[pygame.K_l]:
                        self.load_checkpoints()
                        checkpoints_done = True
                    if checkpoints_done:
                        self.creating_checkpoints = False
            else:
                self.create_start_position(event)
                if ctrl:
                    start_done = False
                    if keys[pygame.K_s]:
                        self.save_start()
                        start_done = True
                    elif keys[pygame.K_l]:
                        self.load_start()
                        start_done = True
                    if start_done:
                        self.player_car = self.initialise_car()
                        self.creating_start = False

            if ctrl and keys[pygame.K_c]:
                self.showing_checkpoints = not self.showing_checkpoints

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
                self.start_angle = math.degrees(math.atan((point2[1] - point1[1]) / (point2[0] - point1[0])))

    def create_checkpoint(self, event: pygame.event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_BUTTON_LEFT:
            self.new_checkpoint_left_point = pygame.mouse.get_pos()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == MOUSE_BUTTON_LEFT:
            self.checkpoints.append((self.new_checkpoint_left_point, pygame.mouse.get_pos()))
            self.new_checkpoint_left_point = None

    def save_checkpoints(self):
        with open("data/track_checkpoints.json", 'w') as file:
            json.dump(self.checkpoints, file)

    def load_checkpoints(self):
        try:
            with open("data/track_checkpoints.json", 'r') as file:
                self.checkpoints = json.load(file)
        except Exception as e:
            print(e)

    def save_start(self):
        self.save_checkpoints()
        with open("data/start.json", 'w') as file:
            json.dump((self.start_position, self.start_angle), file)

    def load_start(self):
        self.load_checkpoints()
        try:
            with open("data/start.json", 'r') as file:
                self.start_position, self.start_angle = json.load(file)
        except Exception as e:
            print(e)

    def start(self):
        self.load_checkpoints()
        self.creating_checkpoints = False
        self.load_start()
        self.creating_start = False
        self.player_car = self.initialise_car()
        self.checkpoint_distance = self.get_distance_from_checkpoint()

    def restart(self):
        self.player_car = self.initialise_car()
        self.checkpoint_distance = self.get_distance_from_checkpoint()
        self.checkpoint_counter = 0

    def step(self, action) -> (int, bool):
        self.clock.tick(60)  # todo move car with delta time?
        self.draw()
        self.handle_events()

        reward = 0
        game_over = False

        if not self.creating_start:
            self.player_car.move_player(action)

            if self.player_car.speed < self.car_max_speed / 10:
                reward = -10

            new_checkpoint_distance = self.get_distance_from_checkpoint()
            reward += self.checkpoint_distance - new_checkpoint_distance

            checkpoint_passed = self.player_car.check_checkpoint_pass(self.checkpoint_distance)
            if checkpoint_passed:
                self.checkpoint_counter += 1
                reward *= 2

            if self.player_car.collide(self.track_border_mask):
                reward = -10
                game_over = True

        return reward, game_over

    def game_loop(self):
        while self.running:
            action = get_human_player_input()
            _, game_over = self.step(action)
            if game_over:
                self.restart()

        pygame.quit()


if __name__ == '__main__':
    game = Drive()
    game.game_loop()
