from datetime import datetime
import os
import torch
import torch.nn as nn
import torch.nn.functional as functional


class LinearQNet(nn.Module):
    def __init__(self, in_size, hidden_size, out_size):
        super().__init__()
        self.linear1 = nn.Linear(in_size, hidden_size)
        self.linear2 = nn.Linear(hidden_size, hidden_size)
        self.linear3 = nn.Linear(hidden_size, out_size)

    def forward(self, tensor):
        tensor = functional.relu(self.linear1(tensor))
        tensor = self.linear2(tensor)
        tensor = self.linear3(tensor)
        return tensor

    def save(self):
        filepath = "model.pt"
        torch.save(self.state_dict(), filepath)
