import shutil
from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'
TARGET = RESULTS / '汇总_mid_5pct'

FILES = [
    (RESULTS / '鲁棒性单语义' / 'robustness_summary_mid_5pct.csv', 'robustness_summary_mid_semantic.csv'),
    (RESULTS / '鲁棒性单语义' / 'robustness_plot_mid_5pct.png', 'robustness_plot_mid_semantic.png'),
    (RESULTS / '鲁棒性双空间' / 'robustness_summary_mid_5pct_both.csv', 'robustness_summary_mid_both.csv'),
    (RESULTS / '鲁棒性双空间' / 'robustness_plot_mid_5pct_both.png', 'robustness_plot_mid_both.png'),
    (RESULTS / '鲁棒性单字符' / 'robustness_summary_mid_5pct_char.csv', 'robustness_summary_mid_char.csv'),
    (RESULTS / '鲁棒性单字符' / 'robustness_plot_mid_5pct_char.png', 'robustness_plot_mid_char.png'),
]


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def assemble():
    ensure_dir(TARGET)
    data_only = TARGET / 'data_only'
    ensure_dir(data_only)

    copied = []
    for src, name in FILES:
        if src.exists():
            dst = TARGET / name
            shutil.copy2(src, dst)
            copied.append(dst)
            if src.suffix == '.csv':
                shutil.copy2(src, data_only / name)

    csvs = list(data_only.glob('*.csv'))
    if csvs:
        dfs = [pd.read_csv(p) for p in csvs]
        combined = pd.concat(dfs, ignore_index=True)
        combined.to_csv(TARGET / 'all_mid_combined.csv', index=False)

    print('Assembled', len(copied), 'files into', TARGET)


if __name__ == '__main__':
    assemble()
