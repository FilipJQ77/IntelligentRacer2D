import json
import math
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import pygame
import pygame_menu

from drive import Drive
from utilities import scale_image, get_human_player_input

CAR = scale_image(pygame.image.load("data/car.png"), 0.6)
CAR_WIDTH = CAR.get_width()
CAR_HEIGHT = CAR.get_height()
TRACK = pygame.image.load("data/track1/track.png")
TRACK_BORDER = pygame.image.load("data/track1/track_border.png")
CHECKPOINTS = json.load(open("data/track1/track_checkpoints.json"))
START_POSITION, START_ANGLE = json.load(open("data/track1/start.json"))
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)
pygame.display.set_caption("Racer 2D")

FPS = 60
WIDTH = TRACK.get_width()
HEIGHT = TRACK.get_height()

MOUSE_BUTTON_LEFT = 1
COLOR_RED = pygame.color.Color(255, 0, 0)
COLOR_BLUE = pygame.color.Color(0, 0, 255)


class OldGame:
    def __init__(self):
        self.window = 420
        self.running = True
        self.clock = pygame.time.Clock()

        self.car_acceleration = 0.7
        self.car_deceleration = 0.2
        self.car_brake_power = 0.5
        self.car_max_speed = 10
        self.car_max_angle = 6

        self.start_angle = 0
        self.start_position = (0, 0)
        self.player_car = None

        self.images = [(TRACK, (0, 0))]
        self.checkpoints = []
        self.new_checkpoint_left_point = None

        self.creating_start = True
        self.creating_checkpoints = True
        self.showing_checkpoints = True

    def initialise_car(self):
        return None
        # return Car(self.car_acceleration,
        #            self.car_deceleration,
        #            self.car_brake_power,
        #            self.car_max_speed,
        #            self.car_max_angle,
        #            self.start_angle,
        #            self.start_position)

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
        with open("data/track1/track_checkpoints.json", 'w') as file:
            json.dump(self.checkpoints, file)

    def load_checkpoints(self):
        try:
            with open("data/track1/track_checkpoints.json", 'r') as file:
                self.checkpoints = json.load(file)
        except Exception as e:
            print(e)

    def save_start(self):
        self.save_checkpoints()
        with open("data/track1/start.json", 'w') as file:
            json.dump((self.start_position, self.start_angle), file)

    def load_start(self):
        self.load_checkpoints()
        try:
            with open("data/track1/start.json", 'r') as file:
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
        self.clock.tick(FPS)
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
            self.checkpoint_distance = new_checkpoint_distance

            checkpoint_passed = self.player_car.check_checkpoint_pass(self.checkpoint_distance)
            if checkpoint_passed:
                self.checkpoint_counter += 1
                reward *= 2

            if self.player_car.collide(TRACK_BORDER_MASK):
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


def get_filename_dialog():
    Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    return askopenfilename()  # show an "Open" dialog box and return the path to the selected file


class Game:
    def __init__(self):
        pygame.init()
        # self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        # self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.window = pygame.display.set_mode((1600, 900))
        self.running = True
        self.track_image = TRACK  # default
        self.track_image_path = None
        self.track_border_image = TRACK_BORDER  # default
        self.track_border_image_path = None
        self.track_checkpoints = CHECKPOINTS  # default
        self.track_checkpoints_path = None
        self.track_start_position = START_POSITION  # default
        self.track_start_angle = START_ANGLE  # default
        self.track_start_path = None
        self.main_menu = self._main_menu()

    def _main_menu(self):
        menu = pygame_menu.Menu(
            title="Intelligent Racer 2D",
            width=self.window.get_width(),
            height=self.window.get_height(),
            theme=pygame_menu.themes.THEME_BLUE,
        )
        menu.add.button("Play", lambda: self.play())
        menu.add.button("Train", self._train_menu())
        menu.add.button("Create a track", lambda: print("Create"))
        menu.add.button("Load a track",
                        self._load_track_menu())
        menu.add.button("Quit", lambda: self.quit())
        return menu

    def _train_menu(self):
        train_menu = pygame_menu.Menu(
            title="Training",
            width=self.window.get_width(),
            height=self.window.get_height(),
            theme=pygame_menu.themes.THEME_BLUE
        )
        train_menu.add.button("Show best player or sth", lambda: print(""))
        return train_menu

    def _load_track_menu(self):
        load_track_menu = pygame_menu.Menu(
            title="Load a track",
            width=self.window.get_width(),
            height=self.window.get_height(),
            theme=pygame_menu.themes.THEME_BLUE,
            columns=2,
            rows=5,
        )
        track_label = load_track_menu.add.label("")
        track_label.update_font({"size": 14})
        button = load_track_menu.add.button("Load track image (PNG)",
                                            lambda: self.load_track(get_filename_dialog(), track_label))
        button.update_font({"size": 14})

        load_track_menu.add.label("")
        track_checkpoints_label = load_track_menu.add.label("")
        track_checkpoints_label.update_font({"size": 14})
        button = load_track_menu.add.button("Load track checkpoints (JSON)",
                                            lambda: self.load_track_checkpoints(get_filename_dialog(),
                                                                                track_checkpoints_label))
        button.update_font({"size": 14})

        track_border_label = load_track_menu.add.label("")
        track_border_label.update_font({"size": 14})
        button = load_track_menu.add.button("Load track border image (PNG)",
                                            lambda: self.load_track_border(get_filename_dialog(), track_border_label))
        button.update_font({"size": 14})

        load_track_menu.add.label("")
        track_start_label = load_track_menu.add.label("")
        track_start_label.update_font({"size": 14})
        button = load_track_menu.add.button("Load track start position (JSON)",
                                            lambda: self.load_track_start(get_filename_dialog(), track_start_label))
        button.update_font({"size": 14})

        return load_track_menu

    def load_assets(self):
        # todo play and train
        print("Loaded assets")
        try:
            self.track_image = pygame.image.load(self.track_image_path)
            self.track_border_image = pygame.image.load(self.track_border_image_path)
            with open(self.track_checkpoints_path, 'r') as file:
                self.track_checkpoints = json.load(file)
            with open(self.track_start_path, 'r') as file:
                self.track_start_position = json.load(file)
        except Exception as e:
            print(e)

    def load_track(self, path, label):
        self.track_image_path = path
        label.set_title(self.track_image_path)

    def load_track_border(self, path, label):
        self.track_border_image_path = path
        label.set_title(self.track_border_image_path)

    def load_track_checkpoints(self, path, label):
        self.track_checkpoints_path = path
        label.set_title(self.track_checkpoints_path)

    def load_track_start(self, path, label):
        self.track_start_path = path
        label.set_title(self.track_start_path)

    def play(self):
        self.load_assets()
        self.main_menu.disable()
        self.running = True
        drive = Drive(self.window, self.track_image, self.track_border_image, CAR, self.track_start_position,
                      self.track_start_angle, self.track_checkpoints, FPS)
        while self.running:
            action = get_human_player_input()
            game_over, stop = drive.step(action)
            if game_over:
                drive.restart()
            if stop:
                self.running = False
                self.main_menu.enable()

    def quit(self):
        self.main_menu.disable()

    def draw(self):
        pass

    def main(self):
        self.main_menu.mainloop(self.window)
        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.main()
