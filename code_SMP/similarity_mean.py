import os
import re
import pickle
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from code_SMP.readSMP import load_all_smp_profiles
from code_automated_correlation.automated_processing import get_offset, align_profiles
from code_SMP.pairs import pairs, first, single_distance_pairs, double_distance_pairs, increasing_distance_pairs, decreasing_distance_pairs
from code_SMP.similarity import similarity, plot_similarity_scores, load_offset_cache, build_pairs_from_list, compute_aligned_correlation_matrix, plot_correlation_matrix


if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()

    for inital_type in ["pairs"]:
        if inital_type == "pairs":
            paired_profiles = build_pairs_from_list(smp_profiles, pairs)
        elif inital_type == "first":
            paired_profiles = build_pairs_from_list(smp_profiles, first)

    data_by_day = {1: [], 2: []}
    mean_profiles = {}
    aligned_profiles = {} #only for type first
    cache_path = "output/similarity_scores/offset_cache.pkl"
    cache = load_offset_cache(cache_path)
    print(f"\nSimilarity scores for manually defined {inital_type} pairs:\n")

    for df1, name1, df2, name2 in paired_profiles:
        # Step 1: crosscorrelate pairs
        #check if crosscorr is already in cache 
        pair_key = tuple(sorted((name1, name2)))
        if pair_key in cache:
            lag = cache[pair_key]["lag"]
        # if not: crosscorrelate 
        else:
            offset_mm, _, lag = get_offset(df1, df2, name1, name2, plot=True)
        # save offset in cache
        cache[pair_key] = {"lag": lag}
        with open(cache_path, "wb") as f:
            pickle.dump(cache, f)

        # Step 2: Align profiles
        df1, df2 = align_profiles(df1, df2, name1, name2, lag, plot=True)

        if inital_type == "first":
            aligned_profiles = (df1, df2)
            continue
        # Step 3: Calculate mean 
        mean_force = (df1["force"].values + df2["force"].values) / 2
        day = df1.attrs.get("date", 0)
        # save in dict
        mean_profiles[name1] = (mean_force, day)
    if inital_type == "first":
        mean = (aligned_profiles[0]["force"].values + aligned_profiles[1]["force"].values) / 2
    for type in ["single", "double", "increasing", "decreasing"]:
        if type == "single":
            paired_means = build_pairs_from_list(mean_profiles, single_distance_pairs)
            #df1 = mean_profiles[0]
        elif type == "double":
            paired_means = build_pairs_from_list(mean_profiles, double_distance_pairs)
        elif type == "increasing":
            paired_means = build_pairs_from_list(mean_profiles, increasing_distance_pairs)
        elif type == "decreasing":
            paired_means = build_pairs_from_list(mean_profiles, decreasing_distance_pairs)

        for df1, name1, df2, name2 in paired_means:
            # step over if pair has none 
            if df1 is None or df2 is None:
                continue
            force1, day1 = df1
            force2, day2 = df2
            
            # Trim to same length
            min_len = min(len(force1), len(force2))

            # Step 4: calculate similarity scores
            cosine = similarity(force1[:min_len], force2[:min_len])

            # get label and day info
            match1 = re.search(r"S\d{2}M\d{4}", name1)
            match2 = re.search(r"S\d{2}M\d{4}", name2)
            label = f"mean{match1.group()[-2:]} - {match2.group()[-2:]}"

            print(f"{label} (Day {day1}):")
            print(f"  Cosine Similarity:   {cosine:.4f}")

            data_by_day[day1].append({
                "label": label,
                "cosine": cosine
            })

        # Step 5: plot similarity scores and save as .txt
        for day in sorted(data_by_day):
            if data_by_day[day]:
                plot_similarity_scores(data_by_day[day], day, alignment=type, savedir="output/similarity_scores/mean")