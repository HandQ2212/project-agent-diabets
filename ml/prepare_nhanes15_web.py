"""Copy a compatible, explicitly selected notebook run for the research demo."""
import argparse
import json
import shutil
from pathlib import Path

from backend.app.nhanes15 import FEATURES


def prepare(source: Path, destination: Path) -> None:
    report = json.loads((source / 'report.json').read_text(encoding='utf-8'))
    if report.get('smoke_test') or report.get('selected_model') != 'neural_seed_42':
        raise ValueError('Run must be a full run whose selected model is neural_seed_42')
    if report.get('features') != FEATURES:
        raise ValueError('Notebook feature order does not match the API contract')
    files = ('report.json', 'preprocessor.joblib', 'neural_seed_42.pt')
    for name in files:
        if not (source / name).is_file():
            raise FileNotFoundError(source / name)
    destination.mkdir(parents=True, exist_ok=False)
    for name in files:
        shutil.copy2(source / name, destination / name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path, help='Explicit notebook run directory')
    parser.add_argument('--destination', type=Path, default=Path('artifacts/nhanes15_web'))
    args = parser.parse_args()
    prepare(args.source, args.destination)
    print(f'Prepared research demo snapshot at {args.destination}')
