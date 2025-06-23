import os
import pickle
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from code_SMP.readSMP import load_all_smp_profiles
from code_SMP.offset import get_offset


def load_offset_cache(cache_path):
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return pickle.load(f)
    return {}



def compute_aligned_correlation_matrix(smp_profiles, day, cache, cache_path):
    day_profiles = {
        name: df for name, df in smp_profiles.items()
        if df.attrs.get("date") == day and df.attrs.get("velocity", 0) != 0
    }

    names = list(day_profiles.keys())
    n = len(names)
    corr_matrix = np.zeros((n, n))

    for i, name1 in enumerate(names):
        for j, name2 in enumerate(names):
            if i <= j:
                df1 = day_profiles[name1]
                df2 = day_profiles[name2]
                pair_key = tuple(sorted((name1, name2)))

                if name1 == name2:
                    corr = 1.0
                else:
                    if pair_key in cache:
                        lag = cache[pair_key]["lag"]
                    else:
                        offset_mm, _, lag = get_offset(df1, df2, name1, name2, plot=False)
                        cache[pair_key] = {"lag": lag}
                        # save offset in cache 
                        with open(cache_path, "wb") as f:
                            pickle.dump(cache, f)


                    df2_aligned = df2.copy()
                    df2_aligned["force"] = df2_aligned["force"].shift(lag, fill_value=0)

                    min_len = min(len(df1), len(df2_aligned))
                    f1 = df1["force"].iloc[:min_len].values
                    f2 = df2_aligned["force"].iloc[:min_len].values
                    corr = np.corrcoef(f1, f2)[0, 1]

                corr_matrix[i, j] = corr
                corr_matrix[j, i] = corr

    return pd.DataFrame(corr_matrix, index=names, columns=names)


def plot_correlation_matrix(corr_df, day):
    """Plot and save the correlation matrix as a heatmap."""
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_df, annot=True, cmap="coolwarm", vmin=-1, vmax=1)
    plt.title(f"Aligned Correlation Matrix - Day {day}")
    plt.tight_layout()
    plt.savefig(f"output/aligned_correlation_matrix_day{day}.png")
    plt.close()

if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()

    cache_path = "output/cross_correlations/offset_cache.pkl"
    offset_cache = load_offset_cache(cache_path)

    for day in [1, 2]:
        corr_df = compute_aligned_correlation_matrix(smp_profiles, day, offset_cache, cache_path)
        plot_correlation_matrix(corr_df, day)
