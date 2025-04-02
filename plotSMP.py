import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path # for os independent path handling
from readSMP import plot_profiles, load_all_smp_profiles


target_dir = Path("output/visualizations")
smp_profiles = load_all_smp_profiles()

all = True
all_day1 = True
all_day2 = True
comparison = True #comparison between two velocities 8mm/s and 20mm/s
temperature_day1 = True #temperature acclimatization 
temperature_day2 = True


#plot all profiles
if all == True: 
    plot_profiles([(df, name) for name, df in smp_profiles.items()], "all_profiles", save=True)

#plot all profiles of a day
if all_day1 == True:
    smp_day1 = {name: df for name, df in smp_profiles.items()
    if df.attrs.get("date") == 1 and df.attrs.get("velocity") != 0}
    plot_profiles([(df, name) for name, df in smp_day1.items()], "day1_profiles", save=True)

if all_day2 == True:
    smp_day2 = {name: df for name, df in smp_profiles.items()
    if df.attrs.get("date") == 2 and df.attrs.get("velocity") != 0}
    plot_profiles([(df, name) for name, df in smp_day2.items()], "day2_profiles", save=True)

# dictionary for velocities
velocity_8 = {name: df for name, df in smp_profiles.items() if df.attrs.get("velocity") == 8}
velocity_20 = {name: df for name, df in smp_profiles.items() if df.attrs.get("velocity") == 20}

def plot_pairs(pairs):
    for name8, (df8, name20, df20) in pairs.items():
        plt.figure(figsize=(8, 5))
        plt.plot(df20["distance"], df20["force"], label=f"{name20} (velocity=20)")
        plt.plot(df8["distance"], df8["force"], label=f"{name8} (velocity=8)")
        plt.xlabel("Distance (mm)")
        plt.ylabel("Force (N)")
        plt.title(f"SMP Signal: {name20} & {name8}")
        plt.legend()
        plt.grid()
        #plt.show()

        # save as figure
        plt.savefig(target_dir / f"comparison_{name20}_{name8}.png")
        plt.close()


#compare two velocities 
if comparison == True:
    # sorted dictionary-names 
    sorted_8 = sorted(velocity_8.keys())
    sorted_20 = sorted(velocity_20.keys())

    paired_profiles = {name8: (velocity_8[name8], name20, velocity_20[name20])
                       for name8, name20 in zip(sorted_8, sorted_20)}
    plot_pairs(paired_profiles)

if temperature_day1 == True:
    smp_day1 = {name: df for name, df in smp_profiles.items()
    if df.attrs.get("date") == 1 and df.attrs.get("velocity") == 0}
    plot_profiles([(df, name) for name, df in smp_day1.items()], "day1_temperature", save=True)

if temperature_day2 == True:
    smp_day1 = {name: df for name, df in smp_profiles.items()
    if df.attrs.get("date") == 2 and df.attrs.get("velocity") == 0}
    plot_profiles([(df, name) for name, df in smp_day1.items()], "day2_temperature", save=True)

