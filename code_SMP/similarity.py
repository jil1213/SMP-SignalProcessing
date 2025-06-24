import os
import re
import pickle
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from scipy.stats import pearsonr
from code_SMP.readSMP import load_all_smp_profiles
from code_SMP.offset import align_profiles, get_offset
from code_SMP.pairs import pairs, first, single_distance_pairs, double_distance_pairs, increasing_distance_pairs, decreasing_distance_pairs


def load_offset_cache(cache_path):
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return pickle.load(f)
    return {}


def build_pairs_from_list(smp_profiles, name_pairs):
    paired_data = []
    for name1, name2 in name_pairs:
        df1 = smp_profiles.get(name1)
        df2 = smp_profiles.get(name2)
        paired_data.append((df1, name1, df2, name2))
    return paired_data


def similarity(df1, df2):
    #make sure they have the same length -I thought they have the same length? Check again!
    #min_len = min(len(df1), len(df2))
    #df1 = df1[:min_len]
    #df2 = df2[:min_len]
    # Pearson Correlation
    pearson_corr, p_value = pearsonr(df1, df2) #is the same as pearson_corr = np.corrcoef(df1, df2)[0, 1] -why is p_value always Zero? 
    # Cosine Similarity
    cosine = np.dot(df1, df2) / (np.linalg.norm(df1) * np.linalg.norm(df2))
    return pearson_corr, p_value, cosine


def plot_similarity_scores(data, day, alignment):
    pair_labels = [entry["label"] for entry in data]
    x = np.arange(len(pair_labels)) * 20  # simulate 20cm spacing
    pearson = [entry["pearson"] for entry in data]
    cosine = [entry["cosine"] for entry in data]
    width = 3

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.set_title(f"Similarity of SMP Profiles aligned {alignment} (Day {day})")
    ax.set_ylabel("Similarity Score")
    ax.set_ylim(0, 1.1)
    ax.set_xticks([])

    # background lines and labels
    for xi, label in zip(x, pair_labels):
        ax.plot([xi, xi], [0, 1], color='lightgray', linestyle='--')
        ax.text(xi, -0.05, label, ha='center', fontsize=7) #change 0.05 to set labels lower if additional distance values

    # plot bars
    ax.bar(x - width, pearson, width=width, label="Pearson")
    ax.bar(x + width, cosine, width=width, label="Cosine")

    ax.legend()
    ax.grid(axis='y')
    plt.tight_layout()
    plt.savefig(f"output/similarity_scores/similarity_plot_day{day}_{alignment}.png")

    # save as txt 
    with open(f"output/similarity_scores/similarity_scores_day{day}_{alignment}.txt", "w") as f:
        f.write(f"Similarity scores for aligned {alignment} - Day {day}:\n\n")
        for entry in data:
            f.write(f"{entry['label']}:\n")
            f.write(f"  Pearson Correlation: {entry['pearson']:.4f} (p-value: {entry['p_value']:.4e})\n")
            f.write(f"  Cosine Similarity:   {entry['cosine']:.4f}\n\n")


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
                        # save offset in cache
                        cache[pair_key] = {"lag": lag}
                        with open(cache_path, "wb") as f:
                            pickle.dump(cache, f)

                    df1, df2 = align_profiles(df1, df2, name1, name2, lag)

                    f1 = df1["force"].values
                    f2 = df2["force"].values
                    corr = np.corrcoef(f1, f2)[0, 1]

                corr_matrix[i, j] = corr
                corr_matrix[j, i] = corr

    return pd.DataFrame(corr_matrix, index=names, columns=names)


def plot_correlation_matrix(corr_df, day):
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_df, annot=True, cmap="coolwarm", vmin=-1, vmax=1)
    plt.title(f"Aligned Correlation Matrix - Day {day}")
    plt.tight_layout()
    plt.savefig(f"output/aligned_correlation_matrix_day{day}.png")
    plt.close()


if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()

    # pairs of profiles saved as lists in code_SMP/pairs.py
    for type in ["pairs", "first", "single", "double", "increasing", "decreasing"]:

        # build pairs for crosscorrelation 
        if type == "pairs":
            paired_profiles = build_pairs_from_list(smp_profiles, pairs)
        elif type == "first":
            paired_profiles = build_pairs_from_list(smp_profiles, first)
        elif type == "double":
            paired_profiles = build_pairs_from_list(smp_profiles, double_distance_pairs)
        elif type == "single":
            paired_profiles = build_pairs_from_list(smp_profiles, single_distance_pairs)
        elif type == "increasing":
            paired_profiles = build_pairs_from_list(smp_profiles, increasing_distance_pairs)
        elif type == "decreasing":
            paired_profiles = build_pairs_from_list(smp_profiles, decreasing_distance_pairs)

        data_by_day = {1: [], 2: []}
        cache_path = "output/similarity_scores/offset_cache.pkl"
        cache = load_offset_cache(cache_path)
        print(f"\nSimilarity scores for manually defined {type} pairs:\n")
        for df1, name1, df2, name2 in paired_profiles:
            # Step 1: crosscorrelate pairs
            #check if crosscorr is already in cache 
            pair_key = tuple(sorted((name1, name2)))
            if pair_key in cache:
                lag = cache[pair_key]["lag"]
            # if not: crosscorrelate 
            else:
                offset_mm, _, lag = get_offset(df1, df2, name1, name2, plot=False)
                # save offset in cache
                cache[pair_key] = {"lag": lag}
                with open(cache_path, "wb") as f:
                    pickle.dump(cache, f)

            # Step 2: Align profiles
            df1, df2 = align_profiles(df1, df2, name1, name2, lag)

            # Step 3: calculate similarity scores
            pearson, p_val, cosine = similarity(df1["force"].values, df2["force"].values)

            # get label and day info
            match1 = re.search(r"S\d{2}M\d{4}", name1)
            match2 = re.search(r"S\d{2}M\d{4}", name2)
            label = f"{match1.group()[-2:]} - {match2.group()[-2:]}"
            day = df1.attrs.get("date", 0)

            print(f"{label} (Day {day}):")
            print(f"  Pearson Correlation: {pearson:.4f} (p-value: {p_val:.4e})")
            print(f"  Cosine Similarity:   {cosine:.4f}\n")

            data_by_day[day].append({
                "label": label,
                "pearson": pearson,
                "cosine": cosine,
                "p_value": p_val
            })

        # Step 4: plot similarity scores and save as .txt
        for day in sorted(data_by_day):
            if data_by_day[day]:
                plot_similarity_scores(data_by_day[day], day, alignment=type, save=True)

        for day in [1, 2]:
            corr_df = compute_aligned_correlation_matrix(smp_profiles, day, cache, cache_path)
            plot_correlation_matrix(corr_df, day)