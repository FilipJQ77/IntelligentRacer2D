import json
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import numpy as np
import pygad
import pygame
import pygame_menu
import torch
from pygad.torchga import torchga

from car import CarSpecification
from create import Create
from drive import Drive
from utilities import scale_image, get_human_player_input, create_action_tuple

pygame.display.set_caption("Intelligent Racer 2D")

FPS = 60
WIDTH = 1600
HEIGHT = 900


def get_filename_dialog():
    Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    return askopenfilename()  # show an "Open" dialog box and return the path to the selected file


def set_label_text(label: pygame_menu.widgets.Label, text):
    label.set_title(text)


class Game:
    def __init__(self):
        pygame.init()
        # self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.car_image = scale_image(pygame.image.load("data/car.png"), 0.5)
        self.track_image_path = "data/track1/track.png"
        self.track_image = pygame.image.load(self.track_image_path)  # default
        self.track_border_image_path = "data/track1/track_border.png"
        self.track_border_image = pygame.image.load(self.track_border_image_path)  # default
        self.track_data_path = "data/track1/track_data.json"
        self.checkpoints, self.start_position, self.start_angle = json.load(open(self.track_data_path))  # default
        self.main_menu = self._main_menu()

        self.ga_instance = None

        self.car_specification = CarSpecification(
            acceleration=0.2,
            deceleration=0.2,
            brake_power=0.5,
            max_speed=10,
            max_angle=4
        )

    def _main_menu(self):
        menu = pygame_menu.Menu(
            title="Intelligent Racer 2D",
            width=self.window.get_width(),
            height=self.window.get_height(),
            theme=pygame_menu.themes.THEME_BLUE,
        )
        menu.add.button("Play", lambda: self.play())
        menu.add.button("Train AI", self._train_menu())
        menu.add.button("Create a track", self._create_track_menu())
        menu.add.button("Load a track", self._load_track_menu())
        menu.add.button("Quit", lambda: self.quit())
        return menu

    def _train_menu(self):
        train_menu = pygame_menu.Menu(
            title="Training",
            width=self.window.get_width(),
            height=self.window.get_height(),
            theme=pygame_menu.themes.THEME_BLUE,

        )
        generation_slider = train_menu.add.range_slider("Number of generations", 100, [i for i in range(1, 501)])
        generation_slider.get_value()
        population_slider = train_menu.add.range_slider("Population size", 50, [i for i in range(10, 201)])

        train_menu.add.button("Train generations",
                              lambda: run_genetic_algorithm(generation_slider.get_value(),
                                                            population_slider.get_value()))

        train_menu.add.button("Show best player", lambda: run_best_player())

        return train_menu

    def _create_track_menu(self):
        create_track_menu = pygame_menu.Menu(
            title="Create a track",
            width=self.window.get_width(),
            height=self.window.get_height(),
            theme=pygame_menu.themes.THEME_BLUE
        )
        track_label = create_track_menu.add.label("")
        create_track_menu.add.button("Load track image to create a track on (PNG)",
                                     lambda: self.load_track(get_filename_dialog(), track_label))

        create_track_menu.add.button("Create a track", self.create_track)

        return create_track_menu

    def _load_track_menu(self):
        load_track_menu = pygame_menu.Menu(
            title="Load a track",
            width=self.window.get_width(),
            height=self.window.get_height(),
            theme=pygame_menu.themes.THEME_BLUE
        )
        track_label = load_track_menu.add.label("")
        load_track_menu.add.button("Load track image (PNG)",
                                   lambda: self.load_track(get_filename_dialog(), track_label))

        track_border_label = load_track_menu.add.label("")
        load_track_menu.add.button("Load track border image (PNG)",
                                   lambda: self.load_track_border(get_filename_dialog(), track_border_label))

        track_data_label = load_track_menu.add.label("")
        load_track_menu.add.button("Load track data (JSON)",
                                   lambda: self.load_track_data(get_filename_dialog(),
                                                                track_data_label))
        return load_track_menu

    def play(self):
        self.main_menu.disable()
        self.window = pygame.display.set_mode((self.track_image.get_width(), self.track_image.get_height()))
        running = True
        # todo tu powinny jakies parametry auta byc przekazywane zamiast tworzone w drive
        drive = Drive(self.window, self.track_image, self.track_border_image, self.car_image, self.car_specification,
                      self.checkpoints, self.start_position, self.start_angle)
        while running:
            self.clock.tick(FPS)
            action = get_human_player_input()
            drive.draw()
            stop = drive.handle_events()
            game_over = drive.step(action)
            if game_over:
                drive.restart()
            if stop:
                running = False
                self.window = pygame.display.set_mode((WIDTH, HEIGHT))

        self.main_menu.enable()

    def create_track(self):
        self.main_menu.disable()
        self.window = pygame.display.set_mode((self.track_image.get_width(), self.track_image.get_height()))
        running = True
        create = Create(self.window, self.track_image)
        while running:
            self.clock.tick(FPS)
            create.draw()
            stop = create.handle_events()
            if stop:
                running = False
                self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        if len(create.checkpoints) < 3 and create.start_position == (0, 0) and create.start_angle == 0:
            print("Incorrect track data")
        else:
            path = "/".join(self.track_image_path.split('/')[:-1])
            with open(f"{path}/track_data.json", 'w') as file:
                json.dump((create.checkpoints, create.start_position, create.start_angle), file)

        self.load_assets()
        self.main_menu.enable()

    def load_track(self, path, label):
        self.track_image_path = path
        self.load_assets()
        set_label_text(label, path)

    def load_track_border(self, path, label):
        self.track_border_image_path = path
        self.load_assets()
        set_label_text(label, path)

    def load_track_data(self, path, label):
        self.track_data_path = path
        self.load_assets()
        set_label_text(label, path)

    def load_assets(self):
        print("Loaded assets")
        try:
            self.track_image = pygame.image.load(self.track_image_path)
            self.track_border_image = pygame.image.load(self.track_border_image_path)
            with open(self.track_data_path, 'r') as file:
                self.checkpoints, self.start_position, self.start_angle = json.load(file)
        except Exception as e:
            print(e)

    def quit(self):
        self.main_menu.disable()

    def main(self):
        self.main_menu.mainloop(self.window)
        pygame.quit()


# because of genetic algorithm library, these need to be global variables
game = Game()


def generate_model(in_size, hidden_size, out_size):
    input_layer = torch.nn.Linear(in_size, hidden_size)
    relu_layer = torch.nn.ReLU()
    output_layer = torch.nn.Linear(hidden_size, out_size)
    return torch.nn.Sequential(input_layer, relu_layer, output_layer)


def get_game_state(driving: Drive):
    # next 3 checkpoints
    len_checkpoints = len(driving.checkpoints)
    checkpoint_1 = driving.checkpoints[driving.checkpoint_counter % len_checkpoints]
    # checkpoint_2 = game.checkpoints[(game.checkpoint_counter + 1) % len_checkpoints]
    # checkpoint_3 = game.checkpoints[(game.checkpoint_counter + 2) % len_checkpoints]

    state = [
        # current car state
        driving.player_car.x,
        driving.player_car.y,
        driving.player_car.angle,
        driving.player_car.speed,

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


def fitness_function(solution, index):
    global game, model
    model_weights_dict = torchga.model_weights_as_dict(model=model,
                                                       weights_vector=solution)

    # Use the current solution as the model parameters.
    model.load_state_dict(model_weights_dict)

    drive = Drive(game.window, game.track_image, game.track_border_image, game.car_image, game.car_specification,
                  game.checkpoints, game.start_position, game.start_angle)

    start_time = pygame.time.get_ticks()

    while True:
        state = torch.tensor(get_game_state(drive), dtype=torch.float)
        prediction = model(state)
        action = create_action_tuple()
        if prediction[0] >= 0:
            action.throttle = 1
        else:
            action.throttle = 0
        if prediction[1] >= 0:
            action.brake = 1
        else:
            action.brake = 0
        if prediction[2] >= 0:
            action.left = 1
        else:
            action.left = 0
        if prediction[3] >= 0:
            action.right = 1
        else:
            action.right = 0
        game_over = drive.step(action)

        current_time = pygame.time.get_ticks()

        if game_over or current_time > start_time + 10_000:  # 10 seconds
            break
    print(f"{index} {drive.checkpoint_counter}")
    return drive.checkpoint_counter


def run_genetic_algorithm(generations, population):
    global game, model
    ga = torchga.TorchGA(model=model, num_solutions=population)
    ga_instance = pygad.GA(num_generations=generations,
                           num_parents_mating=population // 2,
                           initial_population=ga.population_weights,
                           fitness_func=fitness_function,
                           parent_selection_type="sss",
                           crossover_type="single_point",
                           mutation_type="random",
                           mutation_percent_genes=10,
                           keep_parents=-1,
                           on_generation=lambda x: print(
                               f"Generation: {x.generations_completed}\nFitness: {x.best_solution()[1]}\n\n"))

    ga_instance.run()
    ga_instance.plot_fitness()
    game.ga_instance = ga_instance


def run_best_player():
    global game, model
    best_player = game.ga_instance.best_solution()[0]
    model_weights_dict = torchga.model_weights_as_dict(model=model,
                                                       weights_vector=best_player)

    # Use the current solution as the model parameters.
    model.load_state_dict(model_weights_dict)

    game.main_menu.disable()
    game.window = pygame.display.set_mode((game.track_image.get_width(), game.track_image.get_height()))

    drive = Drive(game.window, game.track_image, game.track_border_image, game.car_image, game.car_specification,
                  game.checkpoints, game.start_position, game.start_angle)
    while True:
        state = torch.tensor(get_game_state(drive), dtype=torch.float)
        prediction = model(state)
        # prediction = best_player(state)
        action = create_action_tuple()
        if prediction[0] >= 0:
            action.throttle = 1
        else:
            action.throttle = 0
        if prediction[1] >= 0:
            action.brake = 1
        else:
            action.brake = 0
        if prediction[2] >= 0:
            action.left = 1
        else:
            action.left = 0
        if prediction[3] >= 0:
            action.right = 1
        else:
            action.right = 0

        drive.draw()
        stop = drive.handle_events()
        game_over = drive.step(action)

        if game_over or stop:
            break
    print(f"Best player: {drive.checkpoint_counter}")

    game.window = pygame.display.set_mode((WIDTH, HEIGHT))
    game.main_menu.enable()
    return drive.checkpoint_counter


if __name__ == '__main__':
    game.main()
    # in_size, hidden_size, out_size = 8, 256, 4
    # model = generate_model(8, 256, 4)
    # model2 = generate_model(8, 256, 4)
    # xd = torchga.model_weights_as_vector(model)
    # xd2 = torchga.model_weights_as_vector(model2)
    print("")
