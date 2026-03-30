import argparse
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot_subplots(df, out_png, title_prefix=None):
    df['budget'] = df['budget'].astype(int)
    groups = df.groupby(['ds_temperature','ds_max_length'])

    fig, axes = plt.subplots(1, 3, figsize=(15,4), sharex=True)

    # msr
    ax = axes[0]
    for (temp, maxlen), sub in groups:
        sub_sorted = sub.sort_values('budget')
        ax.plot(sub_sorted['budget'], sub_sorted['msr'], marker='o', label=f"T={temp},L={int(maxlen)}")
    ax.set_xlabel('budget')
    ax.set_ylabel('msr')
    ax.set_title('msr')
    ax.grid(alpha=0.3)

    # aqs
    ax = axes[1]
    for (temp, maxlen), sub in groups:
        sub_sorted = sub.sort_values('budget')
        ax.plot(sub_sorted['budget'], sub_sorted['aqs'], marker='o', label=f"T={temp},L={int(maxlen)}")
    ax.set_xlabel('budget')
    ax.set_ylabel('aqs')
    ax.set_title('aqs')
    ax.grid(alpha=0.3)

    # stealth_mean
    ax = axes[2]
    for (temp, maxlen), sub in groups:
        sub_sorted = sub.sort_values('budget')
        ax.plot(sub_sorted['budget'], sub_sorted['stealth_mean'], marker='o', label=f"T={temp},L={int(maxlen)}")
    ax.set_xlabel('budget')
    ax.set_ylabel('stealth_mean')
    ax.set_title('stealth_mean')
    ax.grid(alpha=0.3)

    axes[2].legend(loc='best', fontsize='small')

    if title_prefix:
        fig.suptitle(title_prefix)

    plt.tight_layout(rect=[0,0,1,0.96])
    plt.savefig(out_png, dpi=150)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--title', help='可选的子图标题前缀')
    args = p.parse_args()

    df = pd.read_csv(args.input)
    plot_subplots(df, args.out, args.title)


if __name__ == '__main__':
    main()
