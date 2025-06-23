import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
from code_SMP.readSMP import load_all_smp_profiles
from code_visualizations.plotSMP import bulid_pairs
from scipy.stats import pearsonr
from code_SMP.pairs import single_distance_pairs, double_distance_pairs, increasing_distance_pairs, decreasing_distance_pairs

#use same logic as in offset.py to build pairs of profiles to a reference profile
def build_daywise_pairs(smp_profiles):
    pairs = []
    for day in [1, 2]:
        # use all profiles except temperature acclimatization
        day_profiles = {name: df for name, df in smp_profiles.items()
            if df.attrs.get("date") == day and df.attrs.get("velocity", 0) != 0}

        reference_name = next(iter(day_profiles))
        reference_df = day_profiles[reference_name]

        for name, df in day_profiles.items():
            if name == reference_name:
                continue  # don' compare with itself
            pairs.append((reference_df, reference_name, df, name))
    return pairs


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


def plot_similarity_scores(data, day, alignment, save=True):
    pair_labels = [entry["label"] for entry in data]
    x = np.arange(len(pair_labels)) * 20  # simulate 20cm spacing
    pearson = [entry["pearson"] for entry in data]
    cosine = [entry["cosine"] for entry in data]
    width = 3

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_title(f"Similarity of SMP Profiles aligned {alignment} (Day {day})")
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
        plt.savefig(f"output/similarity_scores/similarity_plot_day{day}_{alignment}.png")
    else:
        plt.show()

    # save as txt additional:
    with open(f"output/similarity_scores/similarity_scores_day{day}_{alignment}.txt", "w") as f:
        f.write(f"Similarity scores for aligned {alignment} - Day {day}:\n\n")
        for entry in data:
            f.write(f"{entry['label']}:\n")
            f.write(f"  Pearson Correlation: {entry['pearson']:.4f} (p-value: {entry['p_value']:.4e})\n")
            f.write(f"  Cosine Similarity:   {entry['cosine']:.4f}\n\n")


if __name__ == "__main__":
    # I: similarity scores for different velocities: pairs
    # II: similarity scores for profiles aligned to first -> Distance : first 
    # TODO Add cases for all profiles against each others but build crosscorrelation for them first 
    aligned_types = ["pairs", "first"]

    for aligned in aligned_types:
        smp_profiles = load_all_smp_profiles(pnt=False, aligned=aligned)  # load all SMP profiles

        if aligned == "pairs":
            # Create velocity pairs
            paired_profiles = bulid_pairs(smp_profiles)
        else:
            #create pairs with reference profile
            paired_profiles = build_daywise_pairs(smp_profiles)

        # Prepare data for plot
        data_by_day = {1: [], 2: []}

        print(f"\nSimilarity scores for alignment {aligned} type: '\n")
        for df8, name8, df20, name20 in paired_profiles:

            pearson, p_val, cosine = similarity(df8["force"].values, df20["force"].values)

            # get label and day info
            label = f"{name8[-10:-8]} and {name20[-10:-8]}"
            day = df8.attrs.get("date", 0)

            print(f"{label} (Day {day}):")
            print(f"  Pearson Correlation: {pearson:.4f} (p-value: {p_val:.4e})")
            print(f"  Cosine Similarity:   {cosine:.4f}\n")

            data_by_day[day].append({"label": label, "pearson": pearson, "cosine": cosine, "p_value": p_val})

        # plot results per day
        for day in sorted(data_by_day):
            if data_by_day[day]:
                plot_similarity_scores(data_by_day[day], day, alignment=aligned, save=True)
                
    #for nex prfiles paries give them save_dir 
    type = "pairs"  # change this for type 
    save_dir= Path("data/aligned"+type)