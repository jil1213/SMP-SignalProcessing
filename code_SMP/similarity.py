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


def plot_similarity_scores(data, day, save=True):
    pair_labels = [entry["label"] for entry in data]
    x = np.arange(len(pair_labels)) * 20  # simulate 20cm spacing
    pearson = [entry["pearson"] for entry in data]
    cosine = [entry["cosine"] for entry in data]
    width = 3

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_title(f"Similarity of Paired SMP Profiles (aligned)(Day {day})")
    ax.set_ylabel("Similarity Score")
    ax.set_ylim(0, 1.1)
    ax.set_xticks([])

    # background lines and labels
    for xi, label in zip(x, pair_labels):
        ax.plot([xi, xi], [0, 1], color='lightgray', linestyle='--')
        ax.text(xi, -0.05, label, ha='center', fontsize=9) #change 0.05 to set labels lower if additional distance values

    # plot bars
    ax.bar(x - width, pearson, width=width, label="Pearson")
    ax.bar(x + width, cosine, width=width, label="Cosine")

    ax.legend()
    ax.grid(axis='y')
    plt.tight_layout()

    if save:
        plt.savefig(f"output/similarity_scores/similarity_plot_day{day}.png")
    else:
        plt.show()


if __name__ == "__main__":
    # I: similarity scores for different velocities
    smp_profiles = load_all_smp_profiles(pnt=False, aligned="pairs")  # load all SMP profiles

    # Create velocity pairs
    paired_profiles = bulid_pairs(smp_profiles)

    # Prepare data for plot
    results = []
    data_by_day = {1: [], 2: []}

    print("\nSimilarity scores for aligned velocity pairs:\n")
    for df8, name8, df20, name20 in paired_profiles:

        pearson, p_val, cosine = similarity(df8["force"].values, df20["force"].values)
        # get label and day info
        label = f"{name8[-10:-8]} and {name20[-10:-8]}"
        day = df8.attrs.get("date", 0)

        print(f"{label} (Day {day}):")
        print(f"  Pearson Correlation: {pearson:.4f} (p-value: {p_val:.4e})")
        print(f"  Cosine Similarity:   {cosine:.4f}\n")

        data_by_day[day].append({"label": label, "pearson": pearson, "cosine": cosine, "p_value": p_val})

        # store result line
        results.append(f"{label} (Day {day}):\n"
                       f"  Pearson Correlation: {pearson:.4f} (p-value: {p_val:.4e})\n"
                       f"  Cosine Similarity:   {cosine:.4f}\n\n")

    # write results to txt file
    with open("output/similarity_scores/similarity_scores_velocities.txt", "w") as f:
        f.write("Similarity scores for aligned velocity pairs:\n\n")
        f.writelines(results)

    # plot results per day
    for day in sorted(data_by_day):
        if data_by_day[day]:
            plot_similarity_scores(data_by_day[day], day, save=True)

    # II: similarity scores for profiles aligned to first -> Distance 
    load_all_smp_profiles(pnt=False, aligned="first")