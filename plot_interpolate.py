import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
from scipy.signal import argrelextrema
from scipy.interpolate import CubicSpline

from readSMP import load_all_smp_profiles
from offset import align_profiles


#mins interpolate to find trend
#also for temperature measurements (89)


def interpolate(smp_profiles, save=False, target_dir=Path("output/interpolation")):
    target_dir.mkdir(parents=True, exist_ok=True)

    for name, df in smp_profiles.items():
        distance = df["distance"].values
        force = df["force"].values

        # find local minima
        minima_indices = argrelextrema(force, np.less, order=100)[0]  # order can be changed
        minima_distances = distance[minima_indices]
        minima_forces = force[minima_indices]

        # linear interpolation
        fit = np.polyfit(minima_distances, minima_forces, 1) # 1 for linear fit, 2 for quadratic, etc.
        fit_fn = np.poly1d(fit)

        # spline Interpolation
        cs = CubicSpline(minima_distances, minima_forces)
        x_fit = np.linspace(minima_distances.min(), minima_distances.max(), 3) #change for how many segments 
        y_fit = cs(x_fit)

        # Plot
        plt.figure(figsize=(8, 5))
        plt.plot(distance, force, label="SMP Profile")
        plt.plot(minima_distances, minima_forces, 'ro', label="Minima",  markersize=2)

        #linear interpolation
        plt.plot(minima_distances, fit_fn(minima_distances), 'g--', label="Linear Interpolation")
        #spline interpolation
        plt.plot(x_fit, y_fit, 'b--', label="Spline Interpolation")

        plt.xlabel("Distance (mm)")
        plt.ylabel("Force (N)")
        plt.title(f"Interpolierte Minima - {name}")
        plt.legend()
        plt.grid()

        if save==True:
            plt.savefig(target_dir / f"{name}_minima_interpoltated.png")
        else:
            plt.show()
        plt.close()

if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()
    interpolate(smp_profiles, save=True)