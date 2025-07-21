import os
import pickle
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from pathlib import Path
from code_automated_correlation.automated_processing import load_profiles, get_offset, align_profiles


def load_cache(cache_path): #not used in automated codes, only for old versions necessary
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return pickle.load(f)
    return {}


def similarity(df1, df2):
    # Cosine Similarity
    cosine = np.dot(df1, df2) / (np.linalg.norm(df1) * np.linalg.norm(df2))
    return cosine


def compute_aligned_similarity_matrix(smp_profiles, day, save=True, velocity=None):
    if velocity is None:
        day_profiles = smp_profiles
    elif velocity == 0: #only use for my special dataset to devide whole set into subsets (compute for both velocities together)
        day_profiles = {
            name: df for name, df in smp_profiles.items()
            if df.attrs.get("date") == day and df.attrs.get("velocity", 0) != 0}
    else: #only use for my special dataset to devide whole set into subsets
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

                offset_mm, _, lag = get_offset(df1, df2, name1, name2, plot=False)

                df1, df2 = align_profiles(df1, df2, name1, name2, lag, plot=False)

                f1 = df1["force"].values
                f2 = df2["force"].values
                cosine = similarity(f1, f2)

                corr_matrix[i, j] = cosine
                corr_matrix[j, i] = cosine

    if save == True:
        with open(f"code_automated_correlation/output/similarity_scores/corr_data_day{day}.pkl", "wb") as f:
            pickle.dump({"labels": names, "matrix": corr_matrix}, f)

    return pd.DataFrame(corr_matrix, index=names, columns=names)


def plot_correlation_matrix(corr_df, day, velocity=None):
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_df, annot=True, cmap="coolwarm", vmin=0, vmax=1)
    plt.tight_layout()
    if velocity is None:
        plt.title(f"Cosine Correlation Matrix - Day {day}")
        plt.savefig(f"code_automated_correlation/output/similarity_scores/correlation_matrix_day{day}.png")
    elif velocity == 0:
        plt.title(f"Cosine Correlation Matrix - Day {day}")
        plt.savefig(f"output/similarity_scores/correlation_matrix_day{day}.png")
    else:
        plt.title(f"Cosine Correlation Matrix - Day {day}, Velocity {velocity}")
        plt.savefig(f"output/similarity_scores/correlation_matrix_day{day}_v{velocity}.png")
    plt.close()


if __name__ == "__main__":
    root = Path(__file__).resolve().parent 
    input_root = root/ "raw_data"
    output_root = root / "output" / "similarity_scores"
    output_aligned = root / "output" / "crosscorrelation"


    for folder_path in sorted(input_root.iterdir()):
        if folder_path.is_dir():
            day = folder_path.name
            smp_profiles = load_profiles(folder_path)

        corr_df = compute_aligned_similarity_matrix(smp_profiles, day)

        plot_correlation_matrix(corr_df, day)