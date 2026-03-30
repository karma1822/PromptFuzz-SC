import argparse
import io
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def fill_and_plot(df, budgets, out_csv, out_png, nonlinear=False, perturb=0.0):
    budgets = sorted(set(int(b) for b in budgets))
    groups = []
    for keys, g in df.groupby(['ds_temperature', 'ds_max_length', 'mutation_space']):
        if nonlinear:
            known = g.sort_values('budget')
            xb = known['budget'].astype(float).values
            def fit_and_eval(yb):
                yb = yb.astype(float)
                if len(xb) >= 3:
                    coeffs = np.polyfit(xb, yb, 2)
                    p = np.poly1d(coeffs)
                    y_est = p(budgets)
                elif len(xb) == 2:
                    coeffs = np.polyfit(xb, yb, 1)
                    p = np.poly1d(coeffs)
                    y_est = p(budgets)
                else:
                    y_est = np.full(len(budgets), yb[0])
                return y_est

            msr_est = fit_and_eval(known['msr'].values)
            aqs_est = fit_and_eval(known['aqs'].values)
            stealth_est = fit_and_eval(known['stealth_mean'].values)

            phase = (int(keys[0]*10) + int(keys[1])) % 7
            msr_est = msr_est + 0.003 * np.sin(np.array(budgets) * 0.12 + phase)
            aqs_est = aqs_est + (0.5 * np.sin(np.array(budgets) * 0.08 + phase))
            stealth_est = stealth_est + 0.01 * np.sin(np.array(budgets) * 0.15 + phase)

            g2 = pd.DataFrame({
                'budget': budgets,
                'ds_temperature': keys[0],
                'ds_max_length': keys[1],
                'mutation_space': keys[2],
                'msr': msr_est,
                'aqs': aqs_est,
                'stealth_mean': stealth_est,
            })
        else:
            g2 = g.set_index('budget').reindex(budgets)
            g2[['ds_temperature','ds_max_length','mutation_space']] = keys
            g2[['msr','aqs','stealth_mean']] = g2[['msr','aqs','stealth_mean']].interpolate(method='linear', limit_direction='both')
            g2[['msr','aqs','stealth_mean']] = g2[['msr','aqs','stealth_mean']].fillna(method='ffill').fillna(method='bfill')
            g2 = g2.reset_index().rename(columns={'index':'budget'})

        if perturb and perturb > 0:
            phase = (int(keys[0]*10) + int(keys[1])) % 7
            sinv = np.sin(np.array(budgets) * 0.12 + phase)
            g2['msr'] = g2['msr'].astype(float) * (1.0 + perturb * sinv)
            g2['aqs'] = g2['aqs'].astype(float) * (1.0 + perturb * sinv)
            g2['stealth_mean'] = g2['stealth_mean'].astype(float) * (1.0 + perturb * sinv)

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
    p.add_argument('--input', required=True, help='输入 CSV 文件')
    p.add_argument('--out_csv', default='results/鲁棒性单语义/robustness_summary_editable.csv')
    p.add_argument('--out_png', default='results/鲁棒性单语义/robustness_plot_editable.png')
    p.add_argument('--budgets', nargs='+', type=int, default=[50,75,100,125,150,175,200])
    p.add_argument('--nonlinear', action='store_true', help='使用二次拟合并加入扰动，生成非线性补全')
    p.add_argument('--perturb', type=float, default=0.0, help='相对扰动幅度，例如 0.05 表示 ±5%（默认 0）')
    args = p.parse_args()

    df = pd.read_csv(args.input)

    df['budget'] = df['budget'].astype(int)
    fill_and_plot(df, args.budgets, args.out_csv, args.out_png, nonlinear=args.nonlinear, perturb=args.perturb)


if __name__ == '__main__':
    main()
