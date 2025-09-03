import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from code_automated_correlation.a_automated_processing import load_profiles, get_offset, align_profiles
from code_automated_correlation.b_automated_similarity import compute_aligned_similarity_matrix
from code_automated_correlation.c_automated_grouping import analyze_day, find_reference_profile, find_highest_similarity_pairs, find_all_threshold_groups
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
        "std_force": std_force})

    info = {
        "reference_profile": ref_name,
        "aligned_profiles": other_names,
        "mean_similarity": mean_score}

    return result_df, info

def plot_aligned_mean(distance, mean_force, std, group_idx=None, output_dir=None):
    plt.figure(figsize= (5.5,3.5)) #(8, 5))
    label =f"Mean"
    plt.plot(distance, mean_force, label=label)
    plt.fill_between(distance, mean_force - std, mean_force + std, alpha=0.3, label="Standard Deviation")
    plt.xlabel("Distance (mm)")
    plt.ylabel("Force (N)")
    plt.legend()
    plt.grid()
    plt.tight_layout()

    if group_idx is not None:
        plt.savefig(day_output_dir / f"mean_{ref_name}_with_std_group{group_idx}.svg")
    else:
        plt.savefig(day_output_dir / f"mean_{ref_name}_with_std.svg")
    plt.close()


if __name__ == "__main__":

    root = Path(__file__).resolve().parent 
    input_root = root/ "raw_data"
    output_root = root / "output" / "mean"

    for folder_path in sorted(input_root.iterdir()):
        if folder_path.is_dir():
            result = analyze_day(folder_path)

            day = result["day"]
            smp_profiles = result["smp_profiles"]
            S = result["similarity_matrix"]
            labels = result["labels"]
            threshold = result["threshold"]
            ref_result = result["reference_result"]
            pairs = result["pairs"]
            groups = result["groups"]

            # Output directory for current day
            day_output_dir = output_root / day
            day_output_dir.mkdir(parents=True, exist_ok=True)

            # Reference profile for whole day
            ref_name, remaining, mean_score = ref_result

            if ref_name is not None:
                # Compute aligned mean profile
                result_df, info = compute_aligned_mean(smp_profiles, (ref_name, remaining, mean_score))
                print(info)

                # Plot mean with std
                plot_aligned_mean(result_df["distance"], result_df["mean_force"], result_df["std_force"], output_dir=day_output_dir)

                # Plot mean with single profiles
                plt.figure(figsize=(5.5, 3.5))
                for name in [ref_name] + remaining:
                    df = smp_profiles[name]
                    plt.plot(df["distance"][:len(result_df)], df["force"][:len(result_df)], alpha=0.6, label=name)
                plt.plot(result_df["distance"], result_df["mean_force"], label="Mean", color="tab:olive")
                plt.xlabel("Distance (mm)")
                plt.ylabel("Force (N)")
                plt.legend()
                plt.grid()
                plt.tight_layout()
                plt.savefig(day_output_dir / f"mean_{ref_name}_with_profiles.svg")
                plt.close()

            # Pairs of best similarity and build mean for them
            for ref_name, remaining, score in pairs:
                # Compute mean for each pair 
                result_df, info = compute_aligned_mean(smp_profiles, (ref_name, [remaining], score))

                # For Pairs, plot only signals and mean, no std 
                plt.figure(figsize= (5.5,3.5)) #(8, 5))
                #plot single signals
                plt.plot(smp_profiles[ref_name]["distance"][:len(result_df)], smp_profiles[ref_name]["force"][:len(result_df)], alpha=0.6, label=f"{ref_name}")
                plt.plot(smp_profiles[remaining]["distance"][:len(result_df)], smp_profiles[remaining]["force"][:len(result_df)], alpha=0.6, label=f"{remaining}")
                #plot mean
                plt.plot(result_df["distance"], result_df["mean_force"], label="Mean")
                plt.xlabel("Distance (mm)")
                plt.ylabel("Force (N)")
                n_profiles = len(info["aligned_profiles"])
                plt.legend()
                plt.grid()
                plt.tight_layout()
                # Create save path
                filename = f"mean_{ref_name}_{remaining}.svg"
                save_path = day_output_dir / filename
                plt.savefig(save_path)
                plt.close()

            # All groups
            for idx, group in enumerate(groups, 1):
                ref_name, remaining, mean_score = find_reference_profile(group["matrix"], threshold, labels=group["labels"])
                if ref_name is not None:
                    result_df, info = compute_aligned_mean(smp_profiles, (ref_name, remaining, mean_score))
                    #plot_aligned_mean(result_df["distance"], result_df["mean_force"], result_df["std_force"], group_idx=idx)