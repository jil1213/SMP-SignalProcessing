import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path # for os independent path handling
from readSMP import plot_profiles, load_all_smp_profiles, load_pnt


#smp_profiles = {} #dictionary for all smp profiles
#smp_profiles = load_all_smp_profiles()



df_1, name_1 = load_pnt("data/smp_profiles/S45M1058.pnt")
df_2, name_2 = load_pnt("data/smp_profiles/S45M1063.pnt")

#plot_profiles([(df_1, "SMP_1"), (df_2, "SMP_2")], "test_plot.png")


#methods to get the offset of two profiles by autocorrelation
def get_offset(df1, df2):
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
    print(f"Max correlation: {np.max(correlation)}")
    print(f"Offset: {offset_mm:.2f} mm (lag: {lag_max})")

    plt.figure(figsize=(8, 4))
    plt.plot(index_shifts_mm, correlation)
    plt.title("Cross-Correlation over distance")
    plt.xlabel("Distance (mm)")
    plt.ylabel("Correlation")
    plt.grid(True)
    plt.show()

    return offset_mm, correlation, lag_max



offset, corr, lag = get_offset(df_1, df_2)
