import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def fill_and_plot(input_csv, out_csv, out_png, budgets=None):
    df = pd.read_csv(input_csv)
    if budgets is None:
        min_b, max_b = int(df['budget'].min()), int(df['budget'].max())
        budgets = list(range(min_b, max_b + 1, int((max_b - min_b) / 6) or 1))
    budgets = sorted(set(int(b) for b in budgets))

    groups = []
    for keys, g in df.groupby(['ds_temperature', 'ds_max_length', 'mutation_space']):
        g2 = g.set_index('budget').reindex(budgets)
        g2[['ds_temperature','ds_max_length','mutation_space']] = keys
        g2['msr'] = g2['msr'].interpolate(method='linear')
        g2['aqs'] = g2['aqs'].interpolate(method='linear')
        g2['stealth_mean'] = g2['stealth_mean'].interpolate(method='linear')
        g2 = g2.reset_index().rename(columns={'index':'budget'})
        groups.append(g2)

    df_filled = pd.concat(groups, ignore_index=True)
    df_filled = df_filled[['budget','ds_temperature','ds_max_length','mutation_space','msr','aqs','stealth_mean']]
    df_filled.to_csv(out_csv, index=False)

    plt.figure(figsize=(8,5))
    for (temp, maxlen), sub in df_filled.groupby(['ds_temperature','ds_max_length']):
        label = f"T={temp},L={int(maxlen)}"
        sub_sorted = sub.sort_values('budget')
        plt.plot(sub_sorted['budget'], sub_sorted['msr'], marker='o', label=label)

    plt.xlabel('budget')
    plt.ylabel('msr')
    plt.title('Robustness (msr) vs Budget')
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--out_csv', required=True)
    p.add_argument('--out_png', required=True)
    p.add_argument('--budgets', nargs='+', type=int, help='budgets to include (e.g. 50 75 100)')
    args = p.parse_args()
    fill_and_plot(args.input, args.out_csv, args.out_png, args.budgets)


if __name__ == '__main__':
    main()
