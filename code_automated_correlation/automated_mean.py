import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from code_automated_correlation.automated_processing import load_profiles, get_offset, align_profiles
from code_automated_correlation.automated_similarity import compute_aligned_similarity_matrix
from code_automated_correlation.automated_correlation import find_reference_profile, find_highest_similarity_pairs, find_all_threshold_groups
plt.style.use(r'c:/Users/jille/Documents/Uni/Master-Mechatronik/Masterarbeit/SMP-SignalProcessing/latex_default.mplstyle')


def compute_aligned_mean(smp_profiles, values):
    ref_name, other_names, mean_score = values

    df_ref = smp_profiles[ref_name]
    aligned_dfs = [df_ref.reset_index(drop=True)]

    for name in other_names:
        df = smp_profiles[name]

        # calculate lag 
        _, _, lag = get_offset(df_ref, df, ref_name, name, plot=False)
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

def plot_aligned_mean(distance, mean_force, std, info, group_idx=None):
    plt.figure(figsize= (5.5,3.5)) #(8, 5))
    #aligned_block = "\n".join([", ".join(info['aligned_profiles'][i:i+3]) for i in range(0, len(info['aligned_profiles']), 3)])
    # Label with information about averaged profiles
    #label = f"Mean Force\nReference: {info['reference_profile']}\nAligned Profiles:\n{aligned_block}"
    label =f"Mean" #for masterthesis
    plt.plot(distance, mean_force, label=label)
    plt.fill_between(distance, mean_force - std, mean_force + std, alpha=0.3, label="Standard Deviation")
    plt.xlabel("Distance (mm)")
    plt.ylabel("Force (N)")
    n_profiles = len(info["aligned_profiles"])
    #title = f"Mean of \n Reference {info['reference_profile']} with {n_profiles} Profile(s) \nMean Similarity: {info['mean_similarity']:.3f}"
    #plt.title(title)
    plt.legend()
    plt.grid()
    plt.tight_layout()

    # Create save path
    filename = f"mean_{info['reference_profile']}_with_{n_profiles}profiles.svg"
    if group_idx is not None:
        filename = f"group{group_idx}_" + filename
    save_path = "output/automated_mean/" + filename

    plt.savefig(save_path)
    plt.close()


if __name__ == "__main__":

    root = Path(__file__).resolve().parent 
    input_root = root/ "raw_data"
    output_root = root / "output" / "similarity_scores"

    for folder_path in sorted(input_root.iterdir()):
        if folder_path.is_dir():
            day = folder_path.name
            smp_profiles = load_profiles(folder_path)

        # calculate Similarity matrix S and labels
        corr_df = compute_aligned_similarity_matrix(smp_profiles, day)
        S = corr_df.values
        labels = corr_df.index.tolist()

        if day == '20250131': 
            threshold = 0.85 
        else: 
            threshold = 0.75 # good threshold for day 2 , day 1 = 0.85

        # Find reference profile for whole day
        ref_name, remaining, mean_score = find_reference_profile(S, threshold, labels)

        if ref_name is not None:
            # Compute aligned mean profile
            result_df, info = compute_aligned_mean(smp_profiles, (ref_name, remaining, mean_score))
            print(info)
            # Plot the aligned mean profile
            plot_aligned_mean(result_df["distance"], result_df["mean_force"], result_df["std_force"], info)


        # Find Pairs of best similarity and build mean for them
        pairs = find_highest_similarity_pairs(S, labels)
        for ref_name, remaining, score in pairs:
            # Compute mean for each pair 
            result_df, info = compute_aligned_mean(smp_profiles, (ref_name, [remaining], score))

            # For Pairs, plot only signals and mean, no std 
            plt.figure(figsize= (5.5,3.5)) #(8, 5))
            #plot single signals
            plt.plot(smp_profiles[ref_name]["distance"], smp_profiles[ref_name]["force"], label=f"{ref_name}")
            plt.plot(smp_profiles[remaining]["distance"], smp_profiles[remaining]["force"], label=f"{remaining}")
            #plot mean
            plt.plot(result_df["distance"], result_df["mean_force"], label="Mean")
            plt.xlabel("Distance (mm)")
            plt.ylabel("Force (N)")
            n_profiles = len(info["aligned_profiles"])
            plt.legend()
            plt.grid()
            plt.tight_layout()
            # Create save path
            filename = f"mean_{ref_name}_with_{remaining}profiles.svg"
            save_path = "output/automated_mean/" + filename
            plt.savefig(save_path)
            plt.close()

        # Find all groups
        groups = find_all_threshold_groups(S, labels, threshold)

        for idx, group in enumerate(groups, 1):
            ref_name, remaining, mean_score = find_reference_profile(group["matrix"], threshold, labels=group["labels"])
            if ref_name is not None:
                result_df, info = compute_aligned_mean(smp_profiles, (ref_name, remaining, mean_score))
                #plot_aligned_mean(result_df["distance"], result_df["mean_force"], result_df["std_force"], info, group_idx=idx)