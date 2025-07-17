import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from code_SMP.readSMP import load_all_smp_profiles
from code_SMP.offset import align_profiles, get_offset
from code_SMP.similarity import load_offset_cache
from code_SMP.automated_correlation import find_reference_profile


def compute_aligned_mean(indices, labels, cache_path="output/similarity_scores/offset_cache.pkl"):
    ref_index, other_indices, mean_score = indices
    ref_name = labels[ref_index]
    other_names = [labels[i] for i in other_indices]
    all_names = [ref_name] + other_names

    smp_profiles = load_all_smp_profiles(pnt=True)
    df_ref = smp_profiles[ref_name]
    aligned_dfs = [df_ref.reset_index(drop=True)]

    cache = load_offset_cache(cache_path)

    for name in other_names:
        df = smp_profiles[name]
        pair_key = tuple(sorted((ref_name, name)))

        if pair_key in cache:
            lag = cache[pair_key]["lag"]
            # Check if the original key order in cache is reversed (necessary because lags are always defined from lower profile name to higher)
            if (ref_name, name) == (pair_key[1], pair_key[0]):
                # Reverse the sign of lag if names are in opposite order
                lag = -lag
                print(f"Reversed lag for {pair_key}: {lag}")
        else:
            print("There is no lag value in cache for pair ", pair_key)
            exit(0)
            #offset_mm, _, lag = get_offset(df_ref, df, ref_name, name, plot=False)
            #cache[pair_key] = {"lag": lag}
            # Save updated cache
            #with open(cache_path, "wb") as f:
            #    pickle.dump(cache, f)

        _, df_aligned = align_profiles(df_ref, df, ref_name, name, lag, plot=False)
        aligned_dfs.append(df_aligned)

    min_len = min(len(df) for df in aligned_dfs)
    trimmed_forces = np.stack([df["force"].values[:min_len] for df in aligned_dfs])
    distance = aligned_dfs[0]["distance"].values[:min_len]

    mean_force = np.mean(trimmed_forces, axis=0)
    std_force = np.std(trimmed_forces, axis=0, ddof=1)

    result_df = pd.DataFrame({
        "distance": distance,
        "mean_force": mean_force,
        "std_force": std_force
    })

    info = {
        "reference_profile": ref_name,
        "aligned_profiles": all_names,
        "mean_similarity": mean_score}

    return result_df, info


if __name__ == "__main__":

    # Labels for day 1
    labels = [
        "S45M1056", "S45M1057", "S45M1058", "S45M1059", "S45M1060",
        "S45M1061", "S45M1062", "S45M1063", "S45M1064", "S45M1065"
    ]

    # Cosine Similarity Matrix for day 1 
    S = np.array([
        [1.00, 0.91, 0.86, 0.87, 0.81, 0.95, 0.87, 0.91, 0.88, 0.84],
        [0.91, 1.00, 0.82, 0.90, 0.83, 0.90, 0.87, 0.89, 0.87, 0.82],
        [0.86, 0.82, 1.00, 0.82, 0.70, 0.88, 0.82, 0.92, 0.87, 0.83],
        [0.87, 0.90, 0.82, 1.00, 0.84, 0.85, 0.87, 0.85, 0.93, 0.86],
        [0.81, 0.83, 0.70, 0.84, 1.00, 0.79, 0.83, 0.77, 0.81, 0.84],
        [0.95, 0.90, 0.88, 0.85, 0.79, 1.00, 0.87, 0.92, 0.88, 0.81],
        [0.87, 0.87, 0.82, 0.87, 0.83, 0.87, 1.00, 0.81, 0.88, 0.93],
        [0.91, 0.89, 0.92, 0.85, 0.77, 0.92, 0.81, 1.00, 0.85, 0.78],
        [0.88, 0.87, 0.87, 0.93, 0.81, 0.88, 0.88, 0.85, 1.00, 0.90],
        [0.84, 0.82, 0.83, 0.86, 0.84, 0.81, 0.93, 0.78, 0.90, 1.00]
    ])

    #labels for day 2
    labels = [
        "S45M1083", "S45M1084", "S45M1085", "S45M1086", "S45M1087",
        "S45M1089", "S45M1090", "S45M1091", "S45M1092", "S45M1093"
    ]

    # Cosine Similarity Matrix Day 2
    S = np.array([
        [1.00, 0.79, 0.53, 0.75, 0.61, 0.86, 0.59, 0.46, 0.76, 0.62],
        [0.79, 1.00, 0.75, 0.62, 0.68, 0.78, 0.75, 0.56, 0.62, 0.64],
        [0.53, 0.75, 1.00, 0.62, 0.79, 0.59, 0.69, 0.85, 0.62, 0.78],
        [0.75, 0.62, 0.62, 1.00, 0.74, 0.66, 0.64, 0.59, 0.95, 0.82],
        [0.61, 0.68, 0.79, 0.74, 1.00, 0.69, 0.62, 0.73, 0.73, 0.86],
        [0.86, 0.78, 0.59, 0.66, 0.69, 1.00, 0.61, 0.49, 0.67, 0.67],
        [0.59, 0.75, 0.69, 0.64, 0.62, 0.61, 1.00, 0.68, 0.64, 0.68],
        [0.46, 0.56, 0.85, 0.59, 0.73, 0.49, 0.68, 1.00, 0.60, 0.74],
        [0.76, 0.62, 0.62, 0.95, 0.73, 0.67, 0.64, 0.60, 1.00, 0.82],
        [0.62, 0.64, 0.78, 0.82, 0.86, 0.67, 0.68, 0.74, 0.82, 1.00]
    ])


    # good threshold for day 2 , day 1 = 0.85
    threshold = 0.75

    # Find reference profile
    #TO DO: later it can be more than one groups-> iterate over groups/reference profiles
    ref_idx, remaining, mean_score = find_reference_profile(S, threshold, labels)

    if ref_idx is not None:
        print(f"\nSelected reference profile: {labels[ref_idx]}")
        print(f"Remaining profiles: {[labels[i] for i in remaining]}")
        print(f"Mean similarity score: {mean_score:.4f}")

        # Compute aligned mean profile
        result_df, info = compute_aligned_mean((ref_idx, remaining, mean_score), labels)

        print("\nAlignment info:")
        print(info)

        # Plot result
        plt.figure(figsize=(8, 5))
        plt.plot(result_df["distance"], result_df["mean_force"], label="Mean Force")
        plt.fill_between(
            result_df["distance"],
            result_df["mean_force"] - result_df["std_force"],
            result_df["mean_force"] + result_df["std_force"],
            alpha=0.3,
            label="±1 SD"
        )
        plt.xlabel("Distance (mm)")
        plt.ylabel("Force (N)")
        title = f"Mean Profile:\nReference {info['reference_profile']} + {info['aligned_profiles']} \nMean Similarity: {info['mean_similarity']:.3f}"
        plt.title(title)
        plt.legend()
        plt.grid()
        plt.tight_layout()
        #plt.savefig("output/mean_profile.png")
        plt.show()