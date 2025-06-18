import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
from code_SMP.readSMP import load_all_smp_profiles
from code_visualizations.plotSMP import bulid_pairs
from scipy.stats import pearsonr


def similarity(df1, df2):
    #make sure they have the same length -I thought they have the same length? Check again!
    min_len = min(len(df1), len(df2))
    df1 = df1[:min_len]
    df2 = df2[:min_len]
    # Pearson Correlation
    pearson_corr, p_value = pearsonr(df1, df2) #is the same as pearson_corr = np.corrcoef(df1, df2)[0, 1] -why is p_value always Zero? 
    # Cosine Similarity
    cosine = np.dot(df1, df2) / (np.linalg.norm(df1) * np.linalg.norm(df2))
    return pearson_corr, p_value, cosine


def plot_similarity_scores(pair_labels, pearson_list, cosine_list, save=True):

    x = np.arange(len(pair_labels)) * 20  # simulate 20cm spacing
    width = 3

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_title("Similarity of Paired SMP Profiles (aligned)")
    ax.set_ylabel("Similarity Score")
    ax.set_ylim(0, 1.1)
    ax.set_xticks([])

    # background lines and labels
    for xi, label in zip(x, pair_labels):
        ax.plot([xi, xi], [0, 1], color='lightgray', linestyle='--')
        ax.text(xi, -0.05, label, ha='center', fontsize=9) #change 0.05 to set labels lower if additional distance values

    # plot bars
    ax.bar(x - width, pearson_list, width=width, label="Pearson")
    ax.bar(x + width, cosine_list,   width=width, label="Cosine")

    ax.legend()
    ax.grid(axis='y')
    plt.tight_layout()

    if save:
        output_dir = Path("output/similarity_scores")
        output_dir.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_dir / "similarity_plot.png")
    plt.show()


if __name__ == "__main__":
    # start with similarity scores for different velocities
    smp_profiles = load_all_smp_profiles(pnt=False, aligned="pairs")  # load all SMP profiles

    # Create velocity pairs
    paired_profiles = bulid_pairs(smp_profiles)

    # Prepare data for plot
    pair_labels = []
    pearson_list = []
    cosine_list = []

    print("\nSimilarity scores for aligned velocity pairs:\n")
    for df8, name8, df20, name20 in paired_profiles:
        force8 = df8["force"].values
        force20 = df20["force"].values

        pearson, p_val, cosine = similarity(force8, force20)

        print(f"{name8} vs {name20}:")
        print(f"  Pearson Correlation: {pearson:.4f} (p-value: {p_val:.4e})")
        print(f"  Cosine Similarity:   {cosine:.4f}\n")

        pair_labels.append(f"{name8[-10:-8]}–{name20[-10:-8]}") #taking the last two digits of profile name as label
        pearson_list.append(pearson)
        cosine_list.append(cosine)

    plot_similarity_scores(pair_labels, pearson_list, cosine_list, save=True)

    #load_all_smp_profiles(pnt=False, aligned="first")  # load all SMP profiles