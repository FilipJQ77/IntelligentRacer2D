from datetime import datetime
import os
import torch
import torch.nn as nn
import torch.nn.functional as functional


class LinearQNet(nn.Module):
    def __init__(self, in_size, hidden_size, out_size):
        super().__init__()
        self.linear1 = nn.Linear(in_size, hidden_size)
        # self.linear2 = nn.Linear(hidden_size, hidden_size)
        self.linear2 = nn.Linear(hidden_size, out_size)

    def forward(self, tensor):
        tensor = functional.relu(self.linear1(tensor))
        tensor = self.linear2(tensor)
        return tensor

    def save(self, folder_path=r"/model"):
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        filepath = f"{folder_path}/{datetime.today().strftime('%Y-%m-%d-%H:%M:%S')}"
        torch.save(self.state_dict(), filepath)
