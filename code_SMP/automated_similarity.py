import os
import pickle
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from code_SMP.readSMP import load_all_smp_profiles
from code_SMP.offset import align_profiles, get_offset


def load_cache(cache_path):
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return pickle.load(f)
    return {}


def similarity(df1, df2):
    # Cosine Similarity
    cosine = np.dot(df1, df2) / (np.linalg.norm(df1) * np.linalg.norm(df2))
    return cosine


def compute_aligned_correlation_matrix(smp_profiles, day, offset_cache, offset_cache_path, save=True, velocity=None):
    if velocity == 0 or velocity==None: #compute for both velocities together
        day_profiles = {
            name: df for name, df in smp_profiles.items()
            if df.attrs.get("date") == day and df.attrs.get("velocity", 0) != 0}
    else: 
        day_profiles = {
        name: df for name, df in smp_profiles.items()
        if df.attrs.get("date") == day and df.attrs.get("velocity", 0) == velocity}

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
                    cosine = 1.0
                else:
                    if pair_key in offset_cache:
                        lag = offset_cache[pair_key]["lag"]
                    else:
                        offset_mm, _, lag = get_offset(df1, df2, name1, name2, plot=False)
                        # save offset in cache
                        offset_cache[pair_key] = {"lag": lag}
                        with open(offset_cache_path, "wb") as f:
                            pickle.dump(offset_cache, f)

                    df1, df2 = align_profiles(df1, df2, name1, name2, lag)

                    f1 = df1["force"].values
                    f2 = df2["force"].values
                    cosine = similarity(f1, f2)

                corr_matrix[i, j] = cosine
                corr_matrix[j, i] = cosine

    if save == True:
        with open(f"output/similarity_scores/corr_data_day{day}.pkl", "wb") as f:
            pickle.dump({"labels": names, "matrix": corr_matrix}, f)

    return pd.DataFrame(corr_matrix, index=names, columns=names)


def plot_correlation_matrix(corr_df, day, velocity=None):
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_df, annot=True, cmap="coolwarm", vmin=0, vmax=1)
    plt.tight_layout()
    if velocity == 0 or velocity is None:
        plt.title(f"Cosine Correlation Matrix - Day {day}")
        plt.savefig(f"output/similarity_scores/correlation_matrix_day{day}.png")
    else:
        plt.title(f"Cosine Correlation Matrix - Day {day}, Velocity {velocity}")
        plt.savefig(f"output/similarity_scores/correlation_matrix_day{day}_v{velocity}.png")
    plt.close()


if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()
    offset_cache_path = "output/similarity_scores/offset_cache.pkl"
    offset_cache = load_cache(offset_cache_path)
    for day in [1, 2]:
        path = f"output/similarity_scores/corr_data_day{day}.pkl"
        if not os.path.exists(path):
            corr_df = compute_aligned_correlation_matrix(smp_profiles, day, offset_cache, offset_cache_path)
        else: 
            with open(path) as f:
                data = pickle.load(f)
            corr_df = pd.DataFrame(data["matrix"], index=data["labels"], columns=data["labels"])
        plot_correlation_matrix(corr_df, day)