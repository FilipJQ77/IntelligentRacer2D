import random
from collections import deque
import numpy as np
from game import Game

MAX_MEMORY_LEN = 100_000
LONG_MEMORY_LEN = 1000


class Agent:
    def __init__(self):
        self.game_number = 0
        self.epsilon = 0
        self.gamma = 0.9
        self.memory = deque(maxlen=MAX_MEMORY_LEN)
        self.model = None  # TODO
        self.trainer = None  # TODO

    @staticmethod
    def get_state(game: Game):
        # next 3 checkpoints
        len_checkpoints = len(game.checkpoints)
        checkpoint_1 = game.checkpoints[game.checkpoint_index % len_checkpoints]
        checkpoint_2 = game.checkpoints[game.checkpoint_index + 1 % len_checkpoints]
        checkpoint_3 = game.checkpoints[game.checkpoint_index + 2 % len_checkpoints]

        state = [
            # current car state
            game.player_car.x,
            game.player_car.y,
            game.player_car.angle,
            game.player_car.speed,

            # car specification
            game.car_acceleration,
            game.car_deceleration,
            game.car_brake_power,
            game.car_max_speed,
            game.car_max_rotation_speed,

            checkpoint_1[0][0],  # left point x
            checkpoint_1[0][1],  # left point y
            checkpoint_1[1][0],  # right point x
            checkpoint_1[1][1],  # right point y

            checkpoint_2[0][0],  # left point x
            checkpoint_2[0][1],  # left point y
            checkpoint_2[1][0],  # right point x
            checkpoint_2[1][1],  # right point y

            checkpoint_3[0][0],  # left point x
            checkpoint_3[0][1],  # left point y
            checkpoint_3[1][0],  # right point x
            checkpoint_3[1][1],  # right point y
        ]

        return np.array(state, dtype=float)

    def remember(self, state, action, reward, next_state):
        self.memory.append((state, action, reward, next_state))

    def train_short_memory(self, state, action, reward, next_state):
        self.trainer.train_step(state, action, reward, next_state)  # todo

    def train_long_memory(self):
        if len(self.memory) > LONG_MEMORY_LEN:
            sample = random.sample(self.memory, LONG_MEMORY_LEN)
        else:
            sample = self.memory

        states, actions, rewards, next_states = zip(*sample)
        self.trainer.train_steps(states, actions, rewards, next_states)  # todo

    def get_action(self, state):
        pass
