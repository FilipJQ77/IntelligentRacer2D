import copy
import json
import random
import statistics
from datetime import datetime
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import matplotlib.pyplot as plt

import pygame
import pygame_menu
import torch
from pygad.torchga import torchga
from multiprocessing.pool import ThreadPool
import numpy.random as npr

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


def generate_generic_model(in_size, hidden_size, out_size):
    input_layer = torch.nn.Linear(in_size, hidden_size)
    relu_layer = torch.nn.ReLU()
    output_layer = torch.nn.Linear(hidden_size, out_size)
    return torch.nn.Sequential(input_layer, relu_layer, output_layer)


def generate_game_model():
    return generate_generic_model(8, 64, 4)  # todo consider adding 2nd/3rd checkpoint to state


class Game:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.car_image = scale_image(pygame.image.load("data/car.png"), 0.5)
        self.track_image_path = "data/track3/track.png"
        self.track_image = pygame.image.load(self.track_image_path)  # default
        self.track_border_image_path = "data/track3/track_border.png"
        self.track_border_image = pygame.image.load(self.track_border_image_path)  # default
        self.track_data_path = "data/track3/track_data.json"
        self.checkpoints, self.start_position, self.start_angle = json.load(open(self.track_data_path))  # default

        self.generation = 0
        self.generation_stats = []  # (mean, median, best)
        self.population_size = 50
        self.crossover_chance = 0.8
        self.mutation_chance = 0.03
        self.mutation_percent_genes = 0.005
        self.generation_time = 2000
        self.finish_time = pygame.time.get_ticks()

        self.population = None
        self.create_new_population()

        self.car_specification = CarSpecification(
            acceleration=0.2,
            deceleration=0.2,
            brake_power=0.5,
            max_speed=10,
            max_angle=4
        )

        self.main_menu = self._main_menu()

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
        train_menu.add.range_slider("Population size", self.population_size, [i for i in range(10, 501, 2)],
                                    onchange=self.change_generation_size, range_text_value_enabled=False)
        train_menu.add.range_slider("Crossover chance", self.crossover_chance, (0, 1), increment=0.01,
                                    onchange=self.change_crossover_chance)
        train_menu.add.range_slider("Mutation chance", self.mutation_chance, (0, 0.25), increment=0.01,
                                    onchange=self.change_mutation_chance)
        train_menu.add.range_slider("Average percent of genes to mutate", self.mutation_percent_genes, (0, 0.25),
                                    increment=0.01, onchange=self.change_mutation_percent_genes)
        train_menu.add.range_slider("Time for each generation [s]", 2, [i for i in range(0, 31)],
                                    onchange=self.change_generation_time, range_text_value_enabled=False)

        generation_label = train_menu.add.label(f"Generation: {self.generation}")
        mean_label = train_menu.add.label(f"Mean checkpoints: 0")
        median_label = train_menu.add.label(f"Median checkpoints: 0")
        best_label = train_menu.add.label(f"Best checkpoints: 0")

        train_menu.add.button("Create new random population", lambda: self.create_new_population())
        train_menu.add.button("Train 1 generation",
                              lambda: self.train_generations(1, generation_label, mean_label, median_label, best_label))
        train_menu.add.button("Train 10 generations",
                              lambda: self.train_generations(10, generation_label, mean_label, median_label,
                                                             best_label))
        # todo train until stop (hold esc to stop)
        train_menu.add.button("Train 100 generations",
                              lambda: self.train_generations(100, generation_label, mean_label, median_label,
                                                             best_label))
        train_menu.add.button("Show best player", lambda: self.show_player(self.get_best_player_from_population()[0]))
        train_menu.add.button("Save best player model", lambda: self.save_best_player())
        train_menu.add.button("Load model and play it", lambda: self.load_and_show_model())
        train_menu.add.button("Plot training results", lambda: self.plot_generation_stats())

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

    def show_player(self, model):
        self.main_menu.disable()
        self.window = pygame.display.set_mode((self.track_image.get_width(), self.track_image.get_height()))

        drive = Drive(self.window, self.track_image, self.track_border_image, self.car_image, self.car_specification,
                      self.checkpoints, self.start_position, self.start_angle)
        while True:
            state = torch.tensor(drive.get_state(), dtype=torch.float)
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

            drive.draw()
            self.clock.tick(FPS)
            stop = drive.handle_events()
            game_over = drive.step(action)

            if game_over or stop:
                break

        print(f"Number of checkpoints: {drive.checkpoint_counter}")

        self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        self.main_menu.enable()
        return drive.checkpoint_counter

    def get_best_player_from_population(self):
        maxi, index = -1, -1
        for i in range(len(self.population)):
            if self.population[i][1] > maxi:
                maxi = self.population[i][1]
                index = i
        return self.population[index]

    def train_generations(self, number_of_generations, generations_label, mean_label, median_label, best_label):
        for _ in range(number_of_generations):
            self.finish_time = pygame.time.get_ticks() + self.generation_time
            with ThreadPool() as pool:
                # run every AI parallel
                pool.map(self.train_ai, [i for i in range(len(self.population))])

            new_population = []
            best_player = self.get_best_player_from_population()
            # add the best into the population, twice
            new_population.extend([best_player, best_player])

            parents = self.select_parents()
            for i in range(0, len(parents) - 2, 2):
                parent1, parent2 = parents[i], parents[i + 1]
                child1, child2 = self.crossover_model_vectors(parent1, parent2)
                self.mutate_model(child1)
                self.mutate_model(child2)
                child1_model = generate_game_model()
                child2_model = generate_game_model()
                child1_model.load_state_dict(torchga.model_weights_as_dict(child1_model, child1))
                child2_model.load_state_dict(torchga.model_weights_as_dict(child2_model, child2))
                new_population.extend([(child1_model, -1), (child2_model, -1)])

            self.generation += 1
            generation_string = f"Generation: {self.generation}"
            print(generation_string)
            set_label_text(generations_label, generation_string)

            results = [x[1] for x in self.population]
            mean = statistics.mean(results)
            mean_string = f"Mean checkpoints: {mean}"
            print(mean_string)
            set_label_text(mean_label, mean_string)

            median = statistics.median(results)
            median_string = f"Median checkpoints: {median}"
            print(median_string)
            set_label_text(median_label, median_string)

            best = max(results)
            best_string = f"Best checkpoints: {best}"
            print(best_string)
            set_label_text(best_label, best_string)
            print()

            self.generation_stats.append((mean, median, best))

            self.population = new_population

    def create_new_population(self):
        self.population = [(generate_game_model(), -1) for _ in range(self.population_size)]
        self.generation = 0
        self.generation_stats = []

    def train_ai(self, index):
        drive = Drive(self.window, self.track_image, self.track_border_image, self.car_image, self.car_specification,
                      self.checkpoints, self.start_position, self.start_angle)
        model = self.population[index][0]
        while True:
            state = torch.tensor(drive.get_state(), dtype=torch.float)
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

            if pygame.time.get_ticks() > self.finish_time:
                game_over = True

            if game_over:
                break

        self.population[index] = (model, drive.checkpoint_counter)

    def select_parents(self):
        parents = []
        # add the best into the parents
        best_from_population = self.get_best_player_from_population()
        parents.append(torchga.model_weights_as_vector(best_from_population[0]))

        # https://stackoverflow.com/a/52243810
        maxi = sum([x[1] for x in self.population])
        if maxi == 0:
            # if every solution is 'bad' then every solution has equal probability
            maxi = len(self.population)
            selection_probabilities = [1 / maxi for _ in self.population]
        else:
            selection_probabilities = [x[1] / maxi for x in self.population]

        for _ in range(self.population_size - 1):
            parents.append(torchga.model_weights_as_vector(
                self.population[npr.choice(len(self.population), p=selection_probabilities)][0]))

        return parents

    def crossover_model_vectors(self, model_vector1, model_vector2):
        if random.random() > self.crossover_chance:
            return model_vector1, model_vector2
        len_model = len(model_vector1)
        child_vector1 = copy.deepcopy(model_vector1)
        child_vector2 = copy.deepcopy(model_vector2)
        crossover_point1 = random.randint(0, len_model)
        crossover_point2 = random.randint(crossover_point1, len_model)
        for i in range(crossover_point1, crossover_point2):
            child_vector1[i] = model_vector2[i]
            child_vector2[i] = model_vector1[i]
        return child_vector1, child_vector2

    def mutate_model(self, model_vector):
        if random.random() < self.mutation_chance:
            for i in range(len(model_vector)):
                if random.random() < self.mutation_percent_genes:
                    model_vector[i] = random.random() - 0.5  # between -0.5 and 0.5

    def change_generation_size(self, size):
        self.population_size = size

    def change_crossover_chance(self, chance):
        self.crossover_chance = chance

    def change_mutation_chance(self, chance):
        self.mutation_chance = chance

    def change_generation_time(self, time):
        self.generation_time = time * 1000

    def change_mutation_percent_genes(self, percent):
        self.mutation_percent_genes = percent

    def plot_generation_stats(self):
        x_data = [i for i in range(1, self.generation + 1)]
        fig = plt.figure()
        fig.suptitle("Training results")
        plt.xlabel(f"Generation")
        plt.ylabel("Number of checkpoints")
        plt.plot(x_data, [x[0] for x in self.generation_stats], label='Mean')
        plt.plot(x_data, [x[1] for x in self.generation_stats], label='Median')
        plt.plot(x_data, [x[2] for x in self.generation_stats], label='Best')
        plt.legend()
        fig.waitforbuttonpress()

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
                # todo fix angle saving
                json.dump((create.checkpoints, create.start_position, create.start_angle + 270), file)

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

    def save_best_player(self):
        best = self.get_best_player_from_population()[0]
        filepath = f"models/model-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
        torch.save(best.state_dict(), filepath)

    def load_and_show_model(self):
        model_path = get_filename_dialog()
        try:
            model = generate_game_model()
            model.load_state_dict(torch.load(model_path))
            model.eval()
            self.show_player(model)
        except Exception as e:
            print(e)

    def quit(self):
        self.main_menu.disable()

    def main(self):
        self.main_menu.mainloop(self.window)
        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.main()
    # model = generate_model(8, 256, 4)
    # model2 = generate_model(8, 256, 4)
    # xd = torchga.model_weights_as_vector(model)
    # xd2 = torchga.model_weights_as_vector(model2)
    print("")
