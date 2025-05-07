import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from readSMP import plot_profiles, load_all_smp_profiles
from offset import get_offset, overlay_profiles
from plotSMP import bulid_pairs, plot_pairs

#new visualizations for comparison of profiles
target_dir = Path("output/visualizations_new")
smp_profiles = load_all_smp_profiles()

#means of each 5 measurements of one velocity
#errorbars 

for date in [1, 2]:
    smp_day = {name: df for name, df in smp_profiles.items() 
     if df.attrs.get("date") == date and df.attrs.get("velocity") != 0}

    for velocity in [8, 20]:
        subset = {name: df for name, df in smp_day.items() if df.attrs.get("velocity") == velocity}
        # before building mean i have to do an overlaying? ...
        # Mittelwert berechnen, wenn subset nicht leer ist
        # mean of profiles
        mean_df = sum(subset.values()) / len(subset)
        mean_df.attrs["velocity"] = velocity
        mean_df.attrs["date"] = date
        plot_profiles([(mean_df, f"mean_day{date}_velocity{velocity}")], f"day{date}_mean_velocity{velocity}", save=False)


#comparing 8 with 20

#mins interpolate to find trend 
#also for temperature measurements (89)
