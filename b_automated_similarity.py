import os
import pickle
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from pathlib import Path
from a_automated_processing import load_profiles, get_offset, align_profiles


def similarity(df1, df2):
    # Cosine Similarity
    cosine = np.dot(df1, df2) / (np.linalg.norm(df1) * np.linalg.norm(df2))
    return cosine


def compute_aligned_similarity_matrix(smp_profiles, day, save=True, velocity=None, output_dir=None):
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent / "output" / "similarity_scores"
    output_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

    day_profiles = smp_profiles

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
        with open(output_dir / f"corr_data_day{day}.pkl", "wb") as f:
            pickle.dump({"labels": names, "matrix": corr_matrix}, f)

    return pd.DataFrame(corr_matrix, index=names, columns=names)


def plot_correlation_matrix(corr_df, day, velocity=None, output_dir=None):
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent / "output" / "similarity_scores"
    output_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_df, annot=True, cmap="coolwarm", vmin=0, vmax=1, annot_kws={"size": 15})
    plt.tight_layout()
    if velocity is None:
        #plt.title(f"Cosine Correlation Matrix - Day {day}")
        plt.savefig(output_dir / f"correlation_matrix_day{day}.svg")
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
    output_dir = root / "output" / "similarity_scores"


    for folder_path in sorted(input_root.iterdir()):
        if folder_path.is_dir():
            day = folder_path.name
            smp_profiles = load_profiles(folder_path)

        corr_df = compute_aligned_similarity_matrix(smp_profiles, day, output_dir=output_dir)

        plot_correlation_matrix(corr_df, day, output_dir=output_dir)