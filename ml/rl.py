"""Simulated education recommendation via Reinforcement Learning (DQN).
Educational use only; synthetic simulation with zero medical treatment claim.
"""
import json
import logging
from pathlib import Path
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from stable_baselines3 import DQN

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

TOPICS = [
    'Tổng quan về tiểu đường',
    'Ăn uống cân bằng',
    'Vận động thể chất',
    'Theo dõi sức khỏe'
]

class EducationEnv(gym.Env):
    """
    Simulated educational environment.
    State: MultiBinary(4) where 1 indicates an unlearned module, 0 indicates completed.
    Action: Discrete(4) corresponding to selecting one module to deliver.
    Reward: +1.0 if the selected module was needed (state[a] == 1).
            -0.25 if the module was already completed (state[a] == 0).
    Episode ends after 4 interaction steps or when all topics are completed.
    """
    def __init__(self):
        super().__init__()
        self.observation_space = spaces.MultiBinary(4)
        self.action_space = spaces.Discrete(4)
        self.state = np.zeros(4, dtype=np.int8)
        self.steps = 0

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        # Generate random initial needs
        self.state = self.np_random.integers(0, 2, size=4, dtype=np.int8)
        self.steps = 0
        return self.state.copy(), {}

    def step(self, action: int):
        # If all topics already learned, action cannot provide new value
        all_done_before = bool(np.all(self.state == 0))
        
        if self.state[action] == 1:
            reward = 1.0
            self.state[action] = 0  # Marked as learned
        else:
            reward = 0.0 if all_done_before else -0.25
            
        self.steps += 1
        terminated = bool(self.steps >= 4 or np.all(self.state == 0))
        truncated = False
        return self.state.copy(), float(reward), terminated, truncated, {}

def evaluate_policy(policy_fn, episodes=200, base_seed=10000):
    env = EducationEnv()
    returns = []
    for ep in range(episodes):
        seed = base_seed + ep
        obs, _ = env.reset(seed=seed)
        total_reward = 0.0
        for step in range(4):
            action = policy_fn(obs, seed, step)
            obs, reward, terminated, truncated, _ = env.step(int(action))
            total_reward += reward
            if terminated or truncated:
                break
        returns.append(total_reward)
    return float(np.mean(returns)), float(np.std(returns))

def greedy_heuristic(obs, seed, step):
    unlearned = np.where(obs == 1)[0]
    return unlearned[0] if len(unlearned) > 0 else 0

def random_policy(obs, seed, step):
    rng = np.random.default_rng(seed * 31 + step)
    return int(rng.integers(4))

def optimal_oracle(obs, seed, step):
    unlearned = np.where(obs == 1)[0]
    if len(unlearned) > 0:
        return int(unlearned[0])
    return 0

def train_and_evaluate(total_timesteps=30000, output_dir='artifacts/rl'):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    log.info("Initializing DQN training on EducationEnv...")
    train_env = EducationEnv()
    model = DQN(
        'MlpPolicy',
        train_env,
        seed=42,
        learning_starts=200,
        buffer_size=10000,
        batch_size=64,
        gamma=0.99,
        verbose=0
    )
    model.learn(total_timesteps=total_timesteps)
    model.save(str(out / 'education_policy'))
    log.info(f"DQN policy saved to {out / 'education_policy.zip'}")

    # Multi-seed evaluation across 5 distinct test seed sets
    eval_seeds = [1000, 2000, 3000, 4000, 5000]
    dqn_means, dqn_stds = [], []
    random_means, random_stds = [], []
    greedy_means, greedy_stds = [], []
    optimal_means, optimal_stds = [], []

    dqn_policy = lambda obs, s, step: model.predict(obs, deterministic=True)[0]

    for s in eval_seeds:
        m_dqn, s_dqn = evaluate_policy(dqn_policy, episodes=200, base_seed=s)
        m_rnd, s_rnd = evaluate_policy(random_policy, episodes=200, base_seed=s)
        m_grd, s_grd = evaluate_policy(greedy_heuristic, episodes=200, base_seed=s)
        m_opt, s_opt = evaluate_policy(optimal_oracle, episodes=200, base_seed=s)
        
        dqn_means.append(m_dqn)
        random_means.append(m_rnd)
        greedy_means.append(m_grd)
        optimal_means.append(m_opt)

    report = {
        'episodes_per_seed': 200,
        'evaluation_seeds': eval_seeds,
        'topics': TOPICS,
        'state_definition': 'Vector nhị phân 4 chiều [Tổng quan, Ăn uống, Vận động, Theo dõi]; 1 = cần học, 0 = đã hoàn tất.',
        'action_definition': 'Chọn 1 trong 4 chủ đề giáo dục tương ứng với chỉ số [0, 1, 2, 3].',
        'reward_definition': '+1.0 nếu chủ đề đang cần học; -0.25 nếu chọn trùng chủ đề đã hoàn tất; 0.0 khi hoàn tất hết.',
        'results': {
            'dqn_policy': {
                'mean_return': float(np.mean(dqn_means)),
                'std_return': float(np.std(dqn_means))
            },
            'greedy_heuristic': {
                'mean_return': float(np.mean(greedy_means)),
                'std_return': float(np.std(greedy_means))
            },
            'random_baseline': {
                'mean_return': float(np.mean(random_means)),
                'std_return': float(np.std(random_means))
            },
            'optimal_oracle': {
                'mean_return': float(np.mean(optimal_means)),
                'std_return': float(np.std(optimal_means))
            }
        },
        'warning': 'Synthetic reward; simulated educational task, zero evidence of clinical benefit or medical treatment.'
    }

    (out / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report

if __name__ == '__main__':
    train_and_evaluate()
