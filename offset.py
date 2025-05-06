import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
from readSMP import plot_profiles, load_all_smp_profiles, load_pnt
from plotSMP import bulid_pairs

target_dir = Path("output/cross_correlations")
smp_profiles = load_all_smp_profiles()

all = True


#method to get the offset of two profiles by crosscorrelation
def get_offset(df1, df2, name1, name2):
    """Calculate the offset between two profiles using cross-correlation."""

    #Cut dfs to apply autocorrelation - only use for offset method!
    start = 100000
    end = 200000 #100.000 values
    df1_cut = df1.iloc[start:end] #cut out mittle part of profile
    df2_cut = df2.iloc[start:end]

    # mean centering to get a more exact correlation
    #df1_cut["force"] = df1_cut["force"].values - np.mean(df1_cut["force"])
    #df2_cut["force"] = df2_cut["force"].values - np.mean(df2_cut["force"])

    #low-pass filter to get a more exact correlation
    #...

    # Calculate cross-correlation to cutted dfs
    correlation = np.correlate(df1_cut["force"], df2_cut["force"], mode='full')

    dx = np.mean(np.diff(df1_cut["distance"]))  # mean spacing in mm

    index_shifts = np.arange(-len(df1_cut["force"]) + 1, len(df1_cut["force"]))       # create array of right size, starting from -n+1 to n
    index_shifts_mm = index_shifts * dx #convert lags into distances in mm

    lag_max = np.argmax(correlation) - (len(df1_cut["force"]) - 1) #lag with max correlation
    offset_mm = lag_max * dx #distance offset

    #Print results
    print(f"Crosscorrelation {name1} - {name2}")
    print(f"Max corr: {np.max(correlation)}")
    print(f"Offset: {offset_mm:.2f} mm (lag: {lag_max})")

    plt.figure(figsize=(8, 4))
    plt.plot(index_shifts_mm, correlation)
    plt.title(f"Cross-Correlation over distance {name1} & {name2}")
    plt.xlabel("Distance (mm)")
    plt.ylabel("Correlation")
    plt.grid(True)
    #plt.show()
    plt.savefig(target_dir / f"corr_{name1}_{name2}.png")

    return offset_mm, correlation, lag_max



# all profiles comparing two velocites
if all == True:
    paired_profiles = bulid_pairs(smp_profiles)
    for df1, name1, df2, name2 in paired_profiles:
        offset_mm, correlation, lag = get_offset(df1, df2, name1, name2)