import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path 
from readSMP import plot_profiles, load_all_smp_profiles
from plot_interpolate import interpolate
from plotSMP import bulid_pairs, plot_pairs


#load from csv for aligned profiles
smp_profiles = load_all_smp_profiles(pnt=False)

# build velocitiy pairs
paired_profiles = bulid_pairs(smp_profiles)
for df8, name8, df20, name20 in paired_profiles:
    # Interpolate and plot
    df_drift8 = interpolate(name8, df8, save=True)
    df_drift20 = interpolate(name20, df20, save=True)

    title = f"Comparison Interpolated: {name8} vs {name20}"
    filename = f"comparison_interpolated_{name8}_vs_{name20}"
    target_dir = Path("output/interpolation")
    plot_pairs([(df_drift8, name8, df_drift20, name20)], filename=filename, save=False, title=title, target_dir=target_dir)
