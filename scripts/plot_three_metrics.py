import argparse
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot_three(df, out_prefix):
    df['budget'] = df['budget'].astype(int)
    groups = df.groupby(['ds_temperature','ds_max_length'])

    # msr
    plt.figure(figsize=(8,5))
    for (temp, maxlen), sub in groups:
        sub_sorted = sub.sort_values('budget')
        plt.plot(sub_sorted['budget'], sub_sorted['msr'], marker='o', label=f"T={temp},L={int(maxlen)}")
    plt.xlabel('budget')
    plt.ylabel('msr')
    plt.title('Robustness (msr) vs Budget')
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{out_prefix}_msr.png", dpi=150)

    # aqs
    plt.figure(figsize=(8,5))
    for (temp, maxlen), sub in groups:
        sub_sorted = sub.sort_values('budget')
        plt.plot(sub_sorted['budget'], sub_sorted['aqs'], marker='o', label=f"T={temp},L={int(maxlen)}")
    plt.xlabel('budget')
    plt.ylabel('aqs')
    plt.title('Robustness (aqs) vs Budget')
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{out_prefix}_aqs.png", dpi=150)

    # stealth_mean
    plt.figure(figsize=(8,5))
    for (temp, maxlen), sub in groups:
        sub_sorted = sub.sort_values('budget')
        plt.plot(sub_sorted['budget'], sub_sorted['stealth_mean'], marker='o', label=f"T={temp},L={int(maxlen)}")
    plt.xlabel('budget')
    plt.ylabel('stealth_mean')
    plt.title('Robustness (stealth_mean) vs Budget')
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{out_prefix}_stealth.png", dpi=150)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--out_prefix', required=True, help='路径前缀，例如 results/.../robustness_full_char')
    args = p.parse_args()

    df = pd.read_csv(args.input)
    plot_three(df, args.out_prefix)


if __name__ == '__main__':
    main()
