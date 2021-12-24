import random
from collections import deque
import numpy as np
import pygame
import torch

from model import LinearQNet
from trainer import QTrainer
from utilities import choose_action, create_action_tuple

from game import Game

MAX_MEMORY_LEN = 100_000
LONG_MEMORY_LEN = 1000

ONE_THIRD = 1 / 3
TWO_THIRDS = 2 / 3


class Agent:
    def __init__(self, epsilon: float, gamma: float, model: LinearQNet, trainer: QTrainer):
        self.game_number = 0
        self.epsilon = epsilon
        self.gamma = gamma
        self.memory = deque(maxlen=MAX_MEMORY_LEN)
        self.model = model
        self.trainer = trainer

    @staticmethod
    def get_state(game: Game):
        # next 3 checkpoints
        len_checkpoints = len(game.checkpoints)
        checkpoint_1 = game.checkpoints[game.checkpoint_counter % len_checkpoints]
        checkpoint_2 = game.checkpoints[(game.checkpoint_counter + 1) % len_checkpoints]
        checkpoint_3 = game.checkpoints[(game.checkpoint_counter + 2) % len_checkpoints]

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

        return np.array(state, dtype=np.float64)

    def get_action(self, state):
        action = None
        if random.random() < self.epsilon:
            action = create_action_tuple()
            throttle = random.random()
            brake = random.random()
            steering = random.random()

            if throttle > 0.5:
                action.throttle = 1
            else:
                action.throttle = 0

            if brake > 0.5:
                action.brake = 1
            else:
                action.brake = 0

            if steering < ONE_THIRD:
                action.left = 1
                action.right = 0
            elif steering < TWO_THIRDS:
                action.left = 0
                action.right = 1
            else:
                action.left = 0
                action.right = 0

        else:
            state = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state)
            action_index = torch.argmax(prediction).item()
            action = choose_action(action_index)

        return action

    def remember(self, state, action, reward, next_state, game_over):
        self.memory.append((state, action, reward, next_state, game_over))

    def train_short_memory(self, state, action, reward, next_state, game_over):
        self.trainer.train_step(state, action, reward, next_state, game_over)

    def train_long_memory(self):
        if len(self.memory) > LONG_MEMORY_LEN:
            sample = random.sample(self.memory, LONG_MEMORY_LEN)
        else:
            sample = self.memory

        states, actions, rewards, next_states, game_overs = zip(*sample)
        self.trainer.train_steps(states, actions, rewards, next_states, game_overs)


def main():
    epsilon = 1
    learning_rate = 0.001
    gamma = 0.9
    model = LinearQNet(21, 512, 12)
    trainer = QTrainer(model, learning_rate, gamma)
    game = Game()
    agent = Agent(epsilon, gamma, model, trainer)
    game.start()
    while game.running:
        state = Agent.get_state(game)
        action = agent.get_action(state)
        reward, game_over = game.step(action)
        next_state = Agent.get_state(game)

        action_for_training = [action.throttle, action.brake, action.left, action.right]
        agent.train_short_memory(state, action_for_training, reward, next_state, game_over)
        agent.remember(state, action_for_training, reward, next_state, game_over)

        if game_over:
            game.restart()
            agent.game_number += 1
            agent.train_long_memory()
            agent.epsilon *= 0.99
            print(agent.epsilon)

    agent.model.save()
    pygame.quit()


if __name__ == '__main__':
    main()
