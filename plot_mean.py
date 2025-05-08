import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
from readSMP import plot_profiles, load_all_smp_profiles
from offset import get_offset, align_profiles
from plotSMP import bulid_pairs, plot_pairs

def plot_mean(smp_profiles, target_dir=Path("output/visualizations_mean"), save=False, buffer=True):
    """
    Computes and plots the mean SMP profiles per day and velocity.
    Also generates comparison plots between velocities.
    """
    if buffer == True: 
        #take smp_profiles already aligned from cache 
        smp_profiles = load_all_smp_profiles(pnt=False)
    else: 
        # align all profiles to first non-temperature profile before computing mean
        smp_profiles = align_profiles(smp_profiles, pairs=False)

    for date in [1, 2]:
        # Filter profiles of a specific day (excluding temperature measurements)
        smp_day = {name: df for name, df in smp_profiles.items() 
                   if df.attrs.get("date") == date and df.attrs.get("velocity") != 0}
        mean_profiles = {}

        for velocity in [20, 8]:
            subset = {name: df for name, df in smp_day.items() if df.attrs.get("velocity") == velocity}

            #trimm all profiles to the same length = shortest length
            min_len = min(len(df) for df in subset.values())
            subset_trimmed = {name: df.iloc[:min_len].copy() for name, df in subset.items()}

            # check if all have the same length after trimming
            assert all(len(df) == min_len for df in subset_trimmed.values()), "Nicht alle Profile sind gleich lang nach dem Kürzen"

            # save all force values in array
            forces = np.stack([df["force"].values for df in subset_trimmed.values()])
            distance = subset_trimmed[list(subset_trimmed.keys())[0]]["distance"].values

            # Mean and SEM (Standard Error of Mean)
            mean_force = np.mean(forces, axis=0)
            sem = np.std(forces, axis=0, ddof=1) / np.sqrt(forces.shape[0])  

            # Plot Mean with CI 95% 
            plt.figure(figsize=(8, 5))
            plt.plot(distance, mean_force, label=f"Mean (v={velocity})")
            plt.fill_between(distance, mean_force - 1.96 * sem, mean_force + 1.96 * sem, alpha=0.3, label="95% CI")
            plt.xlabel("Distance (mm)")
            plt.ylabel("Force (N)")
            plt.title(f"Mean Profile with 95% CI Day {date}, Velocity {velocity}")
            plt.legend()
            plt.grid()
            if save == True: 
                # save as figure png
                plt.savefig((target_dir / f"mean_day{date}_velocity{velocity}").with_suffix(".png"))
                #save as pdf for better quality in another folder
                (target_dir / "pdf").mkdir(parents=True, exist_ok=True)
                plt.savefig((target_dir / "pdf" / f"mean_day{date}_velocity{velocity}").with_suffix(".pdf"), format="pdf", bbox_inches="tight")
            else:
                plt.show()
            plt.close()

            #save in one array for each velocity
            mean_profiles[velocity] = {"distance": distance,"mean": mean_force,"sem": sem}

        # Plot comparison of mean profiles for velocities 8 and 20
        if 8 in mean_profiles and 20 in mean_profiles:
            plt.figure(figsize=(8, 5))
            for v in [8, 20]:
                dist = mean_profiles[v]["distance"]
                mean = mean_profiles[v]["mean"]
                sem = mean_profiles[v]["sem"]

                plt.plot(dist, mean, label=f"Mean (v={v})")
                plt.fill_between(dist, mean - 1.96 * sem, mean + 1.96 * sem, alpha=0.2, label=f"95% CI (v={v})")

            plt.xlabel("Distance (mm)")
            plt.ylabel("Force (N)")
            plt.title(f"Comparison of Mean Profiles with 95% CI Day {date}")
            plt.legend()
            plt.grid()

            if save==True:
                filename = f"mean_comparison_CI_day{date}"
                plt.savefig(target_dir / f"{filename}.png")
                (target_dir / "pdf").mkdir(parents=True, exist_ok=True)
                plt.savefig(target_dir / "pdf" / f"{filename}.pdf", format="pdf", bbox_inches="tight")
            else:
                plt.show()
            plt.close()

# Beispiel zur Ausführung
if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()
    plot_mean(smp_profiles, save=True)


#means of each 5 measurements of one velocity
#errorbars 

#mins interpolate to find trend 
#also for temperature measurements (89)
