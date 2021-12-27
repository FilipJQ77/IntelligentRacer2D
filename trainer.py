import torch
import torch.nn as nn
import torch.optim as optim
from model import LinearQNet


class QTrainer:
    def __init__(self, model: LinearQNet, learning_rate, gamma):
        self.model = model
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.optimizer = optim.Adam(model.parameters(), self.learning_rate)
        self.criterion = nn.MSELoss()

    def train_step(self, state, action, reward, next_state, game_over):
        states_tensor = torch.unsqueeze(torch.tensor(state, dtype=torch.float), 0)
        actions_tensor = torch.unsqueeze(torch.tensor(action, dtype=torch.long), 0)
        rewards_tensor = torch.unsqueeze(torch.tensor(reward, dtype=torch.long), 0)
        next_states_tensor = torch.unsqueeze(torch.tensor(next_state, dtype=torch.float), 0)
        game_overs = (game_over,)
        self.train(states_tensor, actions_tensor, rewards_tensor, next_states_tensor, game_overs)

    def train_steps(self, states, actions, rewards, next_states, game_overs):
        states_tensor = torch.tensor(states, dtype=torch.float)
        actions_tensor = torch.tensor(actions, dtype=torch.long)
        rewards_tensor = torch.tensor(rewards, dtype=torch.long)
        next_states_tensor = torch.tensor(next_states, dtype=torch.float)
        self.train(states_tensor, actions_tensor, rewards_tensor, next_states_tensor, game_overs)

    def train(self, states_tensor, actions_tensor, rewards_tensor, next_states_tensor, game_overs):
        prediction = self.model(states_tensor)
        target = prediction.clone()
        for i in range(len(states_tensor)):
            new_q = rewards_tensor[i]
            if not game_overs[i]:
                new_q = rewards_tensor[i] + self.gamma * torch.max(self.model(next_states_tensor[i]))

            target[i][torch.argmax(actions_tensor[i])] = new_q

        self.optimizer.zero_grad()
        loss = self.criterion(target, prediction)
        loss.backward()

        self.optimizer.step()
