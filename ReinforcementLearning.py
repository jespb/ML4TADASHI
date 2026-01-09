#!/usr/bin/env python

import argparse
import time
from random import randint, seed

import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from gymnasium import spaces
from tadashi import TrEnum
from tadashi.apps import Polybench

from util import *


class TadashiEnv(gym.Env):
    """
    Custom Gym Environment for Tadashi transformations.
    
    State: The current sequence of transformations applied
    Action: Index of the next transformation to apply from the list of possible transformations
    Reward: Based on validity and speedup (sparse reward at episode end)
    """
    
    def __init__(self, app_factory, n_trials=2, max_steps=20, timeout=99):
        super(TadashiEnv, self).__init__()
        
        self.app_factory = app_factory
        self.n_trials = n_trials
        self.max_steps = max_steps
        self.timeout = timeout
        
        # Current transformation list
        self.transformation_list = []
        
        # Baseline performance (without transformations)
        self.baseline_fitness = None
        
        # Current step count
        self.current_step = 0
        
        # Action space: will be dynamic based on available transformations
        # We'll use a Discrete space with a large upper bound
        self.action_space = spaces.Discrete(1000)
        
        # Observation space: we'll encode the transformation sequence
        # For simplicity, we'll use a fixed-size vector
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(100,), dtype=np.float32
        )
        
        # Cache for possible actions
        self.possible_actions = []
        
    def reset(self, seed=None):
        """Reset the environment to initial state"""
        super().reset(seed=seed)
        
        self.app_factory.reset_scops()
        self.transformation_list = []
        self.current_step = 0
        
        # Calculate baseline if not done yet
        if self.baseline_fitness is None:
            self.baseline_fitness = evaluateList(self.app_factory, [], self.n_trials, self.timeout)
        
        # Get initial possible actions
        self._update_possible_actions()
        
        return self._get_obs(), {}
    
    def _update_possible_actions(self):
        """Update the list of possible actions from current state"""
        self.app_factory.reset_scops()
        scops = self.app_factory.scops[0]
        scops.transform_list(self.transformation_list)
        
        # Get all possible transformations
        self.possible_actions = getAllPossible(self.app_factory, ignore=[])
        
    def _get_obs(self):
        """
        Get current observation (state representation)
        We'll encode the transformation list as a feature vector
        """
        obs = np.zeros(100, dtype=np.float32)
        
        # Encode transformation list length
        obs[0] = len(self.transformation_list)
        
        # Encode last few transformations
        for i, tr in enumerate(self.transformation_list[-10:]):
            if i < 10:
                obs[1 + i * 2] = tr[0]  # node index
                obs[2 + i * 2] = list(TrEnum).index(tr[1]) if isinstance(tr[1], TrEnum) else 0
        
        # Encode number of possible actions
        obs[21] = len(self.possible_actions)
        
        return obs
    
    def step(self, action_index):
        """
        Apply the transformation at action_index
        
        Returns:
            observation, reward, terminated, truncated, info
        """
        self.current_step += 1
        
        # Check if action_index is valid
        if action_index >= len(self.possible_actions):
            # Invalid action - penalize and terminate
            return self._get_obs(), -10.0, True, False, {"valid": False}
        
        # Get the transformation
        node_idx, tr_enum = self.possible_actions[action_index]
        
        # Generate random arguments for this transformation
        self.app_factory.reset_scops()
        scops = self.app_factory.scops[0]
        scops.transform_list(self.transformation_list)
        
        node = scops.schedule_tree[node_idx]
        args = random_args(node, tr_enum)
        
        # Create the transformation
        transformation = [node_idx, tr_enum, *args]
        
        # Check if this transformation is legal
        if not isNextTransformationLegal(self.app_factory, transformation):
            # Invalid transformation - small penalty
            return self._get_obs(), -1.0, False, False, {"valid": False}
        
        # Apply the transformation
        self.transformation_list.append(transformation)
        
        # Update possible actions
        self._update_possible_actions()
        
        # Check termination conditions
        terminated = False
        truncated = False
        
        # Episode ends if no more actions possible or max steps reached
        if len(self.possible_actions) == 0:
            terminated = True
        elif self.current_step >= self.max_steps:
            truncated = True
        
        # Compute reward
        reward = 0.0
        
        # Small positive reward for valid transformation
        reward += 0.1
        
        # If episode is ending, compute final reward based on speedup
        if terminated or truncated:
            final_fitness = evaluateList(
                self.app_factory, self.transformation_list, self.n_trials, self.timeout
            )
            # Fitness is negative (lower is better), baseline is also negative
            # Speedup = baseline_time / current_time = -baseline_fitness / -final_fitness
            speedup = self.baseline_fitness / final_fitness if final_fitness != 0 else 0
            
            # Reward based on speedup (subtract 1 so that 1x speedup = 0 reward)
            reward += (speedup - 1.0) * 10.0
        
        info = {
            "valid": True,
            "transformation_list": self.transformation_list.copy(),
            "num_possible_actions": len(self.possible_actions)
        }
        
        return self._get_obs(), reward, terminated, truncated, info


class PolicyNetwork(nn.Module):
    """Simple policy network for action selection"""
    
    def __init__(self, obs_dim, hidden_dim=128):
        super(PolicyNetwork, self).__init__()
        
        self.network = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1000)  # Max action space size
        )
    
    def forward(self, x, valid_action_mask=None):
        """
        Forward pass
        
        Args:
            x: observation
            valid_action_mask: binary mask of valid actions
        """
        logits = self.network(x)
        
        # Mask invalid actions
        if valid_action_mask is not None:
            logits = logits + (valid_action_mask - 1) * 1e9
        
        return logits


class RLAgent:
    """
    Reinforcement Learning Agent using Policy Gradient (REINFORCE)
    """
    
    def __init__(self, obs_dim, learning_rate=1e-3, gamma=0.99):
        self.policy = PolicyNetwork(obs_dim)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=learning_rate)
        self.gamma = gamma
        
        # Storage for episode
        self.log_probs = []
        self.rewards = []
    
    def select_action(self, state, valid_actions_count):
        """
        Select an action using the current policy
        
        Args:
            state: current observation
            valid_actions_count: number of valid actions
        """
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        
        # Create mask for valid actions
        mask = torch.zeros(1000)
        mask[:valid_actions_count] = 1.0
        
        # Get action probabilities
        logits = self.policy(state_tensor, mask.unsqueeze(0))
        probs = torch.softmax(logits, dim=-1)
        
        # Sample action
        dist = torch.distributions.Categorical(probs)
        action = dist.sample()
        
        # Store log probability
        self.log_probs.append(dist.log_prob(action))
        
        return action.item()
    
    def store_reward(self, reward):
        """Store reward for current step"""
        self.rewards.append(reward)
    
    def update(self):
        """Update policy using collected episode data"""
        if len(self.rewards) == 0:
            return 0.0
        
        # Compute discounted returns
        returns = []
        G = 0
        for r in reversed(self.rewards):
            G = r + self.gamma * G
            returns.insert(0, G)
        
        returns = torch.tensor(returns)
        
        # Normalize returns
        if len(returns) > 1:
            returns = (returns - returns.mean()) / (returns.std() + 1e-8)
        
        # Compute policy loss
        policy_loss = []
        for log_prob, G in zip(self.log_probs, returns):
            policy_loss.append(-log_prob * G)
        
        policy_loss = torch.stack(policy_loss).sum()
        
        # Update policy
        self.optimizer.zero_grad()
        policy_loss.backward()
        self.optimizer.step()
        
        # Clear episode data
        loss_value = policy_loss.item()
        self.log_probs = []
        self.rewards = []
        
        return loss_value


class ReinforcementLearning:
    """Main class for RL-based Tadashi optimization"""
    
    def __init__(self, args):
        seed(args.seed)
        torch.manual_seed(args.seed)
        
        print(f"Opening {args.benchmark}")
        dataset = f"-D{args.dataset}_DATASET"
        oflag = f"-O{args.oflag}"
        print(f"Using {dataset}")
        
        self.app_factory = Polybench(args.benchmark, compiler_options=[dataset, oflag])
        self.app_factory.compile()
        
        self.n_trials = args.n_trials
        self.max_episodes = args.max_gen  # Reusing max_gen as max_episodes
        self.max_steps = args.max_depth  # Reusing max_depth as max_steps per episode
        
        # Create environment
        self.env = TadashiEnv(
            self.app_factory,
            n_trials=self.n_trials,
            max_steps=self.max_steps
        )
        
        # Create agent
        self.agent = RLAgent(
            obs_dim=self.env.observation_space.shape[0],
            learning_rate=1e-3,
            gamma=0.99
        )
        
        self.best_transformation_list = []
        self.best_speedup = 0.0
    
    def fit(self):
        """Train the RL agent"""
        print("\n-----------------------------------------\n[STARTING RL TRAINING]")
        
        # Get baseline
        baseline = evaluateList(self.app_factory, [], self.n_trials)
        print(f"Baseline measure: {baseline}")
        
        for episode in range(self.max_episodes):
            print(f"\nEpisode {episode + 1}/{self.max_episodes}")
            
            # Reset environment
            state, _ = self.env.reset()
            
            episode_reward = 0
            done = False
            truncated = False
            
            # Run episode
            while not (done or truncated):
                # Select action
                num_valid_actions = len(self.env.possible_actions)
                
                if num_valid_actions == 0:
                    break
                
                action = self.agent.select_action(state, num_valid_actions)
                
                # Take step
                next_state, reward, done, truncated, info = self.env.step(action)
                
                # Store reward
                self.agent.store_reward(reward)
                episode_reward += reward
                
                state = next_state
            
            # Update policy
            loss = self.agent.update()
            
            # Get final transformation list
            final_list = self.env.transformation_list
            
            # Evaluate final performance
            if len(final_list) > 0:
                final_fitness = evaluateList(self.app_factory, final_list, self.n_trials)
                speedup = baseline / final_fitness if final_fitness != 0 else 0
                
                print(f"  Episode reward: {episode_reward:.2f}")
                print(f"  Policy loss: {loss:.4f}")
                print(f"  Transformations: {len(final_list)}")
                print(f"  Speedup: {speedup:.3f}x")
                
                # Update best
                if speedup > self.best_speedup:
                    self.best_speedup = speedup
                    self.best_transformation_list = final_list.copy()
                    print(f"  *** New best speedup: {speedup:.3f}x ***")
            else:
                print(f"  Episode reward: {episode_reward:.2f}")
                print(f"  No valid transformations found")
        
        # Print final results
        print("\n-----------------------------------------")
        print("[TRAINING COMPLETE]")
        print(f"\nBest speedup achieved: {self.best_speedup:.3f}x")
        print(f"Best transformation list ({len(self.best_transformation_list)} transformations):")
        print("transformation_list=[")
        for t in self.best_transformation_list:
            print(f"   {t},")
        print("]")
        
        # Verify output correctness
        if len(self.best_transformation_list) > 0:
            arrays_original = self.app_factory.dump_arrays()
            isOutputMatching(arrays_original, self.app_factory, self.best_transformation_list)
        
        print("\n[FINISHED]\n")
