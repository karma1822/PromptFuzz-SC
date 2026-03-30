import argparse
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot_metrics(df, out_msr, out_stealth):
    plt.figure(figsize=(8,5))
    for (temp, maxlen), sub in df.groupby(['ds_temperature','ds_max_length']):
        sub_sorted = sub.sort_values('budget')
        plt.plot(sub_sorted['budget'], sub_sorted['msr'], marker='o', label=f"T={temp},L={int(maxlen)}")
    plt.xlabel('budget')
    plt.ylabel('msr')
    plt.title('Robustness (msr) vs Budget')
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_msr, dpi=150)

    plt.figure(figsize=(8,5))
    for (temp, maxlen), sub in df.groupby(['ds_temperature','ds_max_length']):
        sub_sorted = sub.sort_values('budget')
        plt.plot(sub_sorted['budget'], sub_sorted['stealth_mean'], marker='o', label=f"T={temp},L={int(maxlen)}")
    plt.xlabel('budget')
    plt.ylabel('stealth_mean')
    plt.title('Robustness (stealth_mean) vs Budget')
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_stealth, dpi=150)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--out_msr', default='results/鲁棒性单语义/robustness_msr_mid.png')
    p.add_argument('--out_stealth', default='results/鲁棒性单语义/robustness_stealth_mid.png')
    args = p.parse_args()

    df = pd.read_csv(args.input)
    df['budget'] = df['budget'].astype(int)
    plot_metrics(df, args.out_msr, args.out_stealth)


if __name__ == '__main__':
    main()
