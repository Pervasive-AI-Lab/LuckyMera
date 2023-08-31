from abc import ABC, abstractmethod
import numpy as np
import pickle
import gym
from gym.wrappers import FlattenObservation
from stable_baselines3 import A2C
import torch
from torch.utils.data import Dataset, DataLoader, random_split
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import StepLR

class TrainingAlgorithm(ABC):
    def __init__(self, params, env, checkpoint):
        self.params = params
        self.checkpoint = checkpoint
        self.env = env

    @abstractmethod
    def create_model(self): pass
    
    @abstractmethod
    def train(self): pass

    def evaluate(self, steps=100):
        obs = self.env.reset()
        eval_rewards = []
        for i in range(steps):
            action, _state = self.model.predict(obs)
            obs, reward, done, info = self.env.step(action)
            eval_rewards.append(reward)
            if done:
                print(f"Goal reached in {i} steps.")
                break
        print(f"Average reward per step: {sum(eval_rewards) / len(eval_rewards)}.")

class Trajectory(Dataset):
    def __init__(self, expert_observations, expert_actions):
        self.observations = expert_observations
        self.actions = expert_actions

    def __getitem__(self, index):
        obs = np.concatenate((self.observations['chars'][index], self.observations['colors'][index]), axis=None)
        return obs, self.actions[index]

    def __len__(self):
        return len(self.observations)

class BehavioralCloning(TrainingAlgorithm):
    def __init__(self, params, env_name, dataset, batch_size, checkpoint):
        super().__init__(params, env_name, checkpoint)

        self.use_cuda = self.params['use_cuda'] and torch.cuda_is_available()
        print(f'\n\n\n\n\n\nuse_cuda = {self.use_cuda}\n\n\n\n')

        self.env = FlattenObservation(self.env)
        self.train_loader, self.test_loader = self.create_dataloaders(dataset, batch_size)
        self.model = self.create_model(self.env)

    def create_model(self, env):
        device = 'cuda' if self.use_cuda else 'cpu'
        return A2C('MlpPolicy', env, verbose=1, device=device)
    
    def create_dataloaders(self, dataset, batch_size):
        with open(dataset, 'rb') as fp:
            observations = pickle.load(fp)
        actions = observations.pop('actions')

        dataset = Trajectory(observations, actions)
        train_size = int(0.8 * len(dataset))
        test_size = len(dataset) - train_size
        train_dataset, test_dataset = random_split(dataset, [train_size, test_size])

        train_loader = DataLoader(train_dataset, batch_size, shuffle=True)  
        test_loader = DataLoader(test_dataset, batch_size, shuffle=True)

        return train_loader, test_loader

    def train(self):
        #use_cuda = self.params['use_cuda'] and torch.cuda.is_available()
        torch.manual_seed(self.params['seed'])
        device = torch.device("cuda" if self.use_cuda else "cpu")
        print(f'device for training: {device}')

        #policy = self.model.policy.to(device)

        # loss, optimizer and learning rate scheduler
        loss_fn = nn.CrossEntropyLoss()
        optimizer = optim.Adadelta(self.model.policy.parameters(), lr=self.params['learning_rate'])
        scheduler = StepLR(optimizer, step_size=1, gamma=self.params['scheduler_gamma'])

        # train the policy
        for epoch in range(self.params['epochs']):
            self.train_step(self.model, device, self.train_loader, loss_fn, optimizer)
            self.test_step(self.model, device, self.test_loader, loss_fn)
            scheduler.step()

        self.model.save(self.checkpoint)


    def train_step(self, model, device, train_loader, loss_fn, optimizer):
        model = model.policy.to(device)
        model.train()
        
        for batch_idx, (source, target) in enumerate(train_loader):
            source, target = source.to(device), target.to(device)
            optimizer.zero_grad()
            
            dist = model.get_distribution(source)
            action = dist.distribution.logits
            target = target.long()

            loss = loss_fn(action, target)
            loss.backward()
            optimizer.step()
            
            '''
            if batch_idx % log_interval == 0:
                print(
                    "Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}".format(
                        epoch,
                        batch_idx * len(source),
                        len(train_loader.dataset),
                        100.0 * batch_idx / len(train_loader),
                        loss.item(), ))
            '''
        loss /= len(train_loader)
        print(f"Train set: Average loss: {loss}")

    def test_step(self, model, device, test_loader, loss_fn):
        model = self.model.policy.to(device)
        model.eval()
        test_loss = 0

        with torch.no_grad():
            for source, target in test_loader:
                source, target = source.to(device), target.to(device)

                dist = model.get_distribution(source)
                action = dist.distribution.logits
                target = target.long()

                test_loss = loss_fn(action, target)

        test_loss /= len(test_loader.dataset)
        print(f"Test set: Average loss: {test_loss}")
