import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pathlib import Path
from scipy.signal import argrelextrema
from scipy.interpolate import pchip_interpolate

from readSMP import load_all_smp_profiles

# Interpolation of minima with low pass filter

def interpolate(name, df, plot= False, save=False, target_dir=Path("output/interpolation")):
    target_dir.mkdir(parents=True, exist_ok=True)
    distance = df["distance"].values
    force = df["force"].values
    spatial_res = df.attrs["spatial_resolution"]

    # find local minimas
    minima_indices = argrelextrema(force, np.less, order=int(1/spatial_res))[0]  # sampling finding minimas: order=242, approx. 1mm
    minima_distances = distance[minima_indices]
    minima_forces = force[minima_indices]

    # Interploation
    x_fit = np.linspace(minima_distances.min(), minima_distances.max(), int(minima_distances.max() - minima_distances.min())) #sampling 1mm
    y_fit = pchip_interpolate(minima_distances, minima_forces, x_fit)

    # Low Pass Filter over Interpolation to get flatten curve
    dx = np.mean(np.diff(x_fit))              # Samplingrate of finding local minimas
    moving_window = 10.0                    # size in mm of shot noise moving window 1,5,10mm, not overlapping
    moving_window_minimas = int(moving_window / dx)  # window size adapted to sampling of local minima
    y_smooth = np.convolve(y_fit, np.ones(moving_window_minimas)/moving_window_minimas, mode='same')


    # Plot
    if plot == True:
        plt.figure(figsize=(8, 5))
        plt.plot(distance, force, label="SMP Profile")
        plt.plot(minima_distances, minima_forces, 'ro', label="Minima",  markersize=2)

        # Interpolated minima
        plt.plot(x_fit, y_smooth, 'b--', label="PCHIP Interpolation")

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
    df_drift = pd.DataFrame({"distance": x_fit, "force": y_smooth})
    return df_drift

if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles(pnt=False, aligned="pairs") 
    for name, df in smp_profiles.items():
        interpolate(name, df, plot=True, save=True)