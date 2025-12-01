"""
LSTM-based Reinforcement Learning Module for ANU 6.0
Adaptive learning using LSTM networks and RL for personalized teaching
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random
from typing import Dict, List, Tuple, Optional

class LSTMPolicyNetwork(nn.Module):
    """LSTM-based policy network for adaptive learning"""
    
    def __init__(self, input_size: int = 10, hidden_size: int = 64, 
                 num_actions: int = 5, num_layers: int = 2):
        """
        Initialize LSTM policy network
        
        Args:
            input_size: Size of input features (student state)
            hidden_size: LSTM hidden layer size
            num_actions: Number of possible actions (lesson adjustments)
            num_layers: Number of LSTM layers
        """
        super(LSTMPolicyNetwork, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size, hidden_size, num_layers,
            batch_first=True, dropout=0.2
        )
        
        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size, 128)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, num_actions)
        self.softmax = nn.Softmax(dim=-1)
    
    def forward(self, x, hidden=None):
        """
        Forward pass through network
        
        Args:
            x: Input tensor (batch_size, sequence_length, input_size)
            hidden: Hidden state tuple (h_n, c_n)
        """
        # LSTM forward
        lstm_out, hidden = self.lstm(x, hidden)
        
        # Use last output
        last_output = lstm_out[:, -1, :]
        
        # Fully connected layers
        x = self.fc1(last_output)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        x = self.relu(x)
        x = self.fc3(x)
        
        # Action probabilities
        action_probs = self.softmax(x)
        
        return action_probs, hidden
    
    def init_hidden(self, batch_size: int, device: str = 'cpu'):
        """Initialize hidden state"""
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_size).to(device)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_size).to(device)
        return (h0, c0)

class ReinforcementLearner:
    """Reinforcement Learning agent for adaptive learning"""
    
    def __init__(self, state_size: int = 10, action_size: int = 5,
                 learning_rate: float = 0.001, gamma: float = 0.95,
                 epsilon: float = 1.0, epsilon_decay: float = 0.995,
                 epsilon_min: float = 0.01):
        """
        Initialize RL agent
        
        Args:
            state_size: Size of state vector
            action_size: Number of possible actions
            learning_rate: Learning rate for optimizer
            gamma: Discount factor
            epsilon: Exploration rate
            epsilon_decay: Epsilon decay rate
            epsilon_min: Minimum epsilon value
        """
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        # Device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Policy network
        self.policy_net = LSTMPolicyNetwork(
            input_size=state_size,
            hidden_size=64,
            num_actions=action_size
        ).to(self.device)
        
        # Optimizer
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        
        # Experience replay buffer
        self.memory = deque(maxlen=10000)
        
        # Action meanings
        self.actions = {
            0: 'increase_difficulty',
            1: 'decrease_difficulty',
            2: 'repeat_lesson',
            3: 'change_topic',
            4: 'maintain_current'
        }
    
    def get_state_vector(self, student_data: Dict) -> np.ndarray:
        """
        Convert student data to state vector
        
        Args:
            student_data: Dictionary with student information
        
        Returns:
            State vector as numpy array
        """
        state = np.array([
            student_data.get('avg_pronunciation', 50.0) / 100.0,  # Normalized
            student_data.get('avg_comprehension', 50.0) / 100.0,
            student_data.get('vocabulary_strength', 0.5),
            student_data.get('difficulty_level', 0.5),
            student_data.get('learning_curve', 0.0),
            student_data.get('engagement_score', 0.5),
            student_data.get('error_rate', 0.3),
            student_data.get('session_duration', 0.0) / 3600.0,  # Hours
            student_data.get('lesson_count', 0) / 100.0,  # Normalized
            student_data.get('improvement_rate', 0.0)
        ])
        
        return state
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        Select action using epsilon-greedy policy
        
        Args:
            state: Current state vector
            training: Whether in training mode
        
        Returns:
            Selected action index
        """
        if training and random.random() < self.epsilon:
            return random.randrange(self.action_size)
        
        # Use policy network
        state_tensor = torch.FloatTensor(state).unsqueeze(0).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action_probs, _ = self.policy_net(state_tensor)
            action = torch.multinomial(action_probs, 1).item()
        
        return action
    
    def remember(self, state: np.ndarray, action: int, reward: float,
                next_state: np.ndarray, done: bool):
        """Store experience in replay buffer"""
        self.memory.append((state, action, reward, next_state, done))
    
    def replay(self, batch_size: int = 32):
        """Train on a batch of experiences"""
        if len(self.memory) < batch_size:
            return
        
        batch = random.sample(self.memory, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(np.array(states)).unsqueeze(1).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).unsqueeze(1).to(self.device)
        dones = torch.BoolTensor(dones).to(self.device)
        
        # Get current Q values
        action_probs, _ = self.policy_net(states)
        log_probs = torch.log(action_probs + 1e-8)
        selected_log_probs = log_probs.gather(1, actions.unsqueeze(1)).squeeze(1)
        
        # Calculate returns (discounted rewards)
        returns = []
        G = 0
        for reward, done in zip(reversed(rewards), reversed(dones)):
            if done:
                G = 0
            G = reward + self.gamma * G
            returns.insert(0, G)
        
        returns = torch.FloatTensor(returns).to(self.device)
        returns = (returns - returns.mean()) / (returns.std() + 1e-8)  # Normalize
        
        # Policy gradient loss
        loss = -(selected_log_probs * returns).mean()
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def calculate_reward(self, student_data: Dict, action: int, 
                        next_student_data: Dict) -> float:
        """
        Calculate reward for action
        
        Args:
            student_data: Previous student state
            action: Action taken
            next_student_data: New student state
        
        Returns:
            Reward value
        """
        reward = 0.0
        
        # Improvement in pronunciation
        prev_score = student_data.get('avg_pronunciation', 50.0)
        next_score = next_student_data.get('avg_pronunciation', 50.0)
        improvement = next_score - prev_score
        reward += improvement * 0.5
        
        # Engagement bonus
        engagement = next_student_data.get('engagement_score', 0.5)
        reward += engagement * 0.3
        
        # Penalty for wrong difficulty
        difficulty = next_student_data.get('difficulty_level', 0.5)
        if difficulty > 0.9 or difficulty < 0.1:
            reward -= 0.2
        
        # Bonus for maintaining good performance
        if next_score >= 80:
            reward += 0.2
        
        return reward
    
    def get_action_description(self, action: int) -> str:
        """Get human-readable action description"""
        return self.actions.get(action, 'unknown')
    
    def save_model(self, filepath: str):
        """Save trained model"""
        torch.save({
            'policy_state_dict': self.policy_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, filepath)
    
    def load_model(self, filepath: str):
        """Load trained model"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint['policy_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint.get('epsilon', self.epsilon_min)

