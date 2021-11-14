from collections import deque

from game import Game

MAX_MEMORY_LEN = 100_000


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
        car_x = game.player_car.x
        car_y = game.player_car.y
        car_angle = game.player_car.angle
        """
        (x, y, angle) - car
        (acceleration, deceleration, brake power, max velocity, max rotation velocity) - car parameters
        (left: (x, y), right: (x, y)) - checkpoint - 3 next checkpoints to cross
        """
