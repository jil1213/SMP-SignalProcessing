import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from code_SMP.readSMP import load_all_smp_profiles
from code_SMP.offset import align_profiles, get_offset
from code_SMP.similarity import load_offset_cache
from code_SMP.automated_correlation import find_reference_profile, find_highest_similarity_pairs, find_all_threshold_groups


def compute_aligned_mean(smp_profiles, values, cache_path="output/similarity_scores/offset_cache.pkl"):
    ref_name, other_names, mean_score = values

    df_ref = smp_profiles[ref_name]
    aligned_dfs = [df_ref.reset_index(drop=True)]

    cache = load_offset_cache(cache_path)

    for name in other_names:
        df = smp_profiles[name]
        pair_key = tuple(sorted((ref_name, name)))

        if pair_key in cache:
            lag = cache[pair_key]["lag"]
            # Check if the original key order in cache is reversed 
            # !necessary because lags are always defined from lower profile name to higher
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

    # Cut all profiles to same min length
    min_len = min(len(df) for df in aligned_dfs)
    trimmed_forces = np.stack([df["force"].values[:min_len] for df in aligned_dfs])
    distance = aligned_dfs[0]["distance"].values[:min_len]

    # Compute mean and std
    mean_force = np.mean(trimmed_forces, axis=0)
    std_force = np.std(trimmed_forces, axis=0, ddof=1)

    result_df = pd.DataFrame({
        "distance": distance,
        "mean_force": mean_force,
        "std_force": std_force
    })

    info = {
        "reference_profile": ref_name,
        "aligned_profiles": other_names,
        "mean_similarity": mean_score}

    return result_df, info

def plot_aligned_mean(distance, mean_force, std, info):
    plt.figure(figsize=(8, 5))
    aligned_block = "\n".join([", ".join(info['aligned_profiles'][i:i+3]) for i in range(0, len(info['aligned_profiles']), 3)])
    # Label with information about averaged profiles
    label = f"Mean Force\nReference: {info['reference_profile']}\nAligned Profiles:\n{aligned_block}"
    plt.plot(distance, mean_force, label=label)
    plt.fill_between(distance, mean_force - std, mean_force + std, alpha=0.3, label="±1 SD")
    plt.xlabel("Distance (mm)")
    plt.ylabel("Force (N)")
    n_profiles = len(info["aligned_profiles"])
    title = f"Mean of \n Reference {info['reference_profile']} with {n_profiles} Profile(s) \nMean Similarity: {info['mean_similarity']:.3f}"
    plt.title(title)
    plt.legend()
    plt.grid()
    plt.tight_layout()

    # Create save path
    filename = f"mean_{info['reference_profile']}_with_{n_profiles}profiles.png"
    save_path = "output/automated_mean/" + filename

    plt.savefig(save_path)


if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles(pnt=True)

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

    # good threshold for day 2 , day 1 = 0.85
    threshold = 0.85

    # Find reference profile for whole day
    ref_name, remaining, mean_score = find_reference_profile(S, threshold, labels)

    if ref_name is not None:
        print(f"\nSelected reference profile: {ref_name}")
        print(f"Remaining profiles: {remaining}")
        print(f"Mean similarity score: {mean_score:.4f}")

        # Compute aligned mean profile
        result_df, info = compute_aligned_mean(smp_profiles, (ref_name, remaining, mean_score))

        # Plot the aligned mean profile
        plot_aligned_mean(result_df["distance"], result_df["mean_force"], result_df["std_force"], info)

    # Find Pairs of best similarity and build mean for them
    pairs = find_highest_similarity_pairs(S, labels)
    print(pairs)
    for ref_name, remaining, score in pairs:
        print(f"{ref_name} - {remaining}: Similarity = {score:.4f}")
        # Compute mean for each pair 
        result_df, info = compute_aligned_mean(smp_profiles, (ref_name, [remaining], score))
        # Plot the aligned mean profile for each pair
        plot_aligned_mean(result_df["distance"], result_df["mean_force"], result_df["std_force"], info)
