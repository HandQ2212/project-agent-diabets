"""Simulated education recommendation, never a treatment policy."""
import json
from pathlib import Path
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from stable_baselines3 import DQN

TOPICS = ['Tổng quan về tiểu đường', 'Ăn uống cân bằng', 'Vận động thể chất', 'Theo dõi sức khỏe']

class EducationEnv(gym.Env):
    def __init__(self):
        self.observation_space = spaces.MultiBinary(4)
        self.action_space = spaces.Discrete(4)
        self.state = np.zeros(4, dtype=np.int8)
        self.steps = 0
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.state = self.np_random.integers(0, 2, size=4, dtype=np.int8)
        self.steps = 0
        return self.state.copy(), {}
    def step(self, action):
        reward = 1.0 if self.state[action] == 1 else -0.25
        self.state[action] = 0
        self.steps += 1
        return self.state.copy(), reward, self.steps >= 4, False, {}

def evaluate(policy, episodes=200):
    env = EducationEnv(); returns = []
    for seed in range(10000, 10000 + episodes):
        obs, _ = env.reset(seed=seed); total = 0
        for step in range(4):
            action = policy(obs, seed, step)
            obs, reward, done, _, _ = env.step(int(action)); total += reward
        returns.append(total)
    return float(np.mean(returns))

if __name__ == '__main__':
    Path('artifacts/rl').mkdir(parents=True, exist_ok=True)
    model = DQN('MlpPolicy', EducationEnv(), seed=42, learning_starts=200, buffer_size=10000, batch_size=64, verbose=0)
    model.learn(total_timesteps=30000); model.save('artifacts/rl/education_policy')
    learned = evaluate(lambda obs, seed, step: model.predict(obs, deterministic=True)[0])
    random_score = evaluate(lambda obs, seed, step: np.random.default_rng(seed * 10 + step).integers(4))
    report = {'episodes': 200, 'mean_reward_rl': learned, 'mean_reward_random': random_score, 'warning': 'Synthetic reward; not evidence of clinical benefit.'}
    Path('artifacts/rl/report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
