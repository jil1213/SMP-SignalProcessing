import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pickle

from pathlib import Path
from scipy.signal import argrelextrema

from code_SMP.readSMP import load_all_smp_profiles
from code_SMP.pairs import pairs
from code_automated_correlation.automated_processing import get_offset, align_profiles
from code_SMP.similarity import load_offset_cache, build_pairs_from_list

# Interpolation of minima with low pass filter

def interpolate(name, df, plot= False, save=False, target_dir=Path("output/interpolation")):
    target_dir.mkdir(parents=True, exist_ok=True)
    distance = df["distance"].values
    force = df["force"].values
    spatial_res = df.attrs["spatial_resolution"]

    #smooth force over 1mm window
    window_size = int(1 / spatial_res)  # window size adapted to sampling of local minima
    force = np.convolve(force, np.ones(window_size)/window_size, mode="same")

    # find local minimas
    minima_indices = argrelextrema(force, np.less, order=int(1/spatial_res))[0]  # sampling finding minimas: order=242, approx. 1mm
    minima_distances = distance[minima_indices]
    minima_forces = force[minima_indices]

    #find lowest two indices 
    profile_midpoint = distance.max() / 2

    # Indizes der tiefsten Minima in jeder Hälfte
    idx_first = np.where(minima_distances <= profile_midpoint)[0][np.argmin(minima_forces[minima_distances <= profile_midpoint])]
    idx_second = np.where(minima_distances > profile_midpoint)[0][np.argmin(minima_forces[minima_distances > profile_midpoint])]

    lowest_indices = [idx_first, idx_second]

    # Punkte extrahieren
    x_points = minima_distances[lowest_indices]
    y_points = minima_forces[lowest_indices]

    # Lineare Fit-Koeffizienten bestimmen (y = m*x + b)
    coeffs = np.polyfit(x_points, y_points, deg=1)

    # Trendlinie berechnen
    y_trend = np.polyval(coeffs, distance)

    # Plot
    if plot == True:
        plt.figure(figsize=(8, 5))
        plt.plot(distance, force, label="SMP Profile")
        plt.plot(minima_distances, minima_forces, 'ro', label="Minima",  markersize=2)

        # Interpolated minima
        plt.plot(x_points, y_points, 'go', label="Lowest Minima", markersize=5)
        plt.plot(distance, y_trend, 'b--', label="Low Pass Filtered Interpolation")
        plt.xlabel("Distance (mm)")
        plt.ylabel("Force (N)")
        plt.title(f"Interpolate minima with low pass filter- {name}")
        plt.legend()
        plt.grid()

        if save==True:
            plt.savefig(target_dir / f"{name}_minima_interpoltated.png")
        else:
            plt.show()
        plt.close()
    df_drift = pd.DataFrame({"distance": distance, "force": y_trend})
    return df_drift

if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()

    # build pairs for crosscorrelation - pairs of profiles saved as lists in code_SMP/pairs.py
    paired_profiles = build_pairs_from_list(smp_profiles, pairs)
    
    data_by_day = {1: [], 2: []}
    cache_path = "output/similarity_scores/offset_cache.pkl"
    cache = load_offset_cache(cache_path)
    for df1, name1, df2, name2 in paired_profiles:
        # Step 1: crosscorrelate pairs
        #check if crosscorr is already in cache 
        pair_key = tuple(sorted((name1, name2)))
        if pair_key in cache:
            lag = cache[pair_key]["lag"]
        # if not: crosscorrelate 
        else:
            offset_mm, _, lag = get_offset(df1, df2, name1, name2, plot=True)
        # save offset in cache
        cache[pair_key] = {"lag": lag}
        with open(cache_path, "wb") as f:
            pickle.dump(cache, f)

        # Step 2: Align profiles
        df1, df2 = align_profiles(df1, df2, name1, name2, lag, plot=True)

        # Step 3: Interpolate minima
        df1_drift = interpolate(name1, df1, plot=True, save=True)
        df2_drift = interpolate(name2, df2, plot=True, save=True)
        
        # Step 4 plot both drifts together 
        plt.figure(figsize=(8, 5))
        plt.plot(df1_drift["distance"], df1_drift["force"], label=name1)
        plt.plot(df2_drift["distance"], df2_drift["force"], label=name2)
        plt.xlabel("Distance (mm)")
        plt.ylabel("Force (N)")
        plt.title(f"Comparison of drift curves {name1} and {name2}")
        plt.legend()
        plt.grid()
        plt.savefig(f"output/interpolation/drift_{name1}_{name2}.png")
