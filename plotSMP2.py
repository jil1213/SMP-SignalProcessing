import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
from readSMP import plot_profiles, load_all_smp_profiles
from offset import get_offset, align_profiles
from plotSMP import bulid_pairs, plot_pairs

def plot_mean(smp_profiles, target_dir=Path("output/visualizations_new"), save=False):
    """
    Computes and plots the mean SMP profiles per day and velocity.
    Also generates comparison plots between velocities.
    """

    for date in [1, 2]:
        # Filter profiles of a specific day (excluding temperature measurements)
        smp_day = {name: df for name, df in smp_profiles.items() 
                   if df.attrs.get("date") == date and df.attrs.get("velocity") != 0}
        mean_profiles = {}

        for velocity in [8, 20]:
            subset = {name: df for name, df in smp_day.items() if df.attrs.get("velocity") == velocity}
            
            if not subset:
                continue

            #overlay profiles before computing mean
            # subset = align_profiles(subset)

            # Compute mean profile
            mean_df = sum(subset.values()) / len(subset)
            mean_df.attrs["velocity"] = velocity
            mean_df.attrs["date"] = date

            # Plot mean profile for individual velocity
            plot_profiles([(mean_df, f"mean_day{date}_velocity{velocity}")],
                          f"day{date}_mean_velocity{velocity}", save=False, target_dir=target_dir)

            mean_profiles[velocity] = mean_df

        # Comparison plot of both velocities
        if 8 in mean_profiles and 20 in mean_profiles:
            plot_pairs([(mean_profiles[8], f"mean_day{date}", 
                         mean_profiles[20], f"mean_day{date}")],
                       filename=f"mean_comparison_day{date}",
                       title=f"Comparison of means of day {date}",
                       save=False, target_dir=target_dir)

# Beispiel zur Ausführung
if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()
    plot_mean(smp_profiles, save=True)
    

#means of each 5 measurements of one velocity
#errorbars 

#mins interpolate to find trend 
#also for temperature measurements (89)
