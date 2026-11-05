"""Inference contract for the notebook's 15-variable NHANES research model."""
from torch import nn

FEATURES = [
    'RIDAGEYR', 'RIAGENDR', 'BMXBMI', 'BMXWAIST', 'BPXSY1', 'BPXDI1',
    'LBXGLU', 'LBXGH', 'LBXTC', 'LBDHDD', 'LBXTR', 'LBXSATSI', 'LBXSCR',
    'BMXWT', 'BMXHT',
]

BOUNDS = {
    'RIDAGEYR': (18, 80), 'RIAGENDR': (1, 2), 'BMXBMI': (10, 100),
    'BMXWAIST': (30, 250), 'BPXSY1': (50, 300), 'BPXDI1': (20, 200),
    'LBXGLU': (40, 500), 'LBXGH': (3, 20), 'LBXTC': (50, 800),
    'LBDHDD': (5, 200), 'LBXTR': (10, 3000), 'LBXSATSI': (1, 1000),
    'LBXSCR': (0.1, 15), 'BMXWT': (20, 350), 'BMXHT': (100, 250),
}


class NotebookCNN(nn.Module):
    """Architecture defined in notebooks/training/04_NHANES_15_Chi_So.ipynb."""
    def __init__(self, n: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Unflatten(1, (1, n)), nn.Conv1d(1, 16, 3, padding=1), nn.ReLU(),
            nn.Conv1d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool1d(2),
            nn.Flatten(), nn.Linear(32 * (n // 2), 32), nn.ReLU(),
            nn.Dropout(.2), nn.Linear(32, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)
