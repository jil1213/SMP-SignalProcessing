import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from snowmicropyn import Profile
from readSMP import load_all_smp_profiles



def detect_surface(df):
    distance = df["distance"]
    force = df["force"]

    # filter to only positive values for log calculation
    mask = force > 0
    log_force = np.log(force[mask])
    log_distance = distance[mask]

    # calculate gradient
    gradient = np.gradient(log_force, log_distance)
    start_idx = np.searchsorted(log_distance, 20)
    dx = np.mean(np.diff(log_distance))              # Samplingrate of finding local minimas
    window_size_mm = 10.0                    # size in mm of shot noise moving window 1,5,10mm, not overlapping
    window_size = int(window_size_mm / dx)  # window size adapted to sampling of local minima

    for i in range(start_idx + 50, len(gradient) - window_size):
        mean_prev = np.mean(gradient[start_idx:i])  # mean
        mean_window = np.mean(gradient[i:i + window_size])  # current window

        if mean_window > mean_prev *2:  # change value for sensitivtiy
            surface = log_distance[i]
            break

    return surface

def detect_surface2(profile):
    #compare with snowmicropyn package detection method
    surface2 = profile.detect_surface()
    return surface2

def plot_surface(df, name, surface): 
    plt.figure(figsize=(8, 5))
    plt.plot(df["distance"], df["force"])
    plt.axvline(x=surface, color='red', linestyle='--', label=f'Surface: {surface} mm')
    #plt.axvline(x=surface2, color='blue', linestyle='--', label=f'Surface: {surface2} mm')
    plt.yscale('log')
    plt.xlabel("Distance (mm)")
    plt.ylabel("Force log (N)")
    plt.title(f"Profile: {name}")
    plt.grid()
    plt.legend()
    plt.show()

if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles(pnt=True)
    for name, df in smp_profiles.items():
        surface = detect_surface(df)
        print(f"Profile: {name}, Detected Surface: {surface} mm")
        #does not work yet because you need snowmicropyn profile
        #surface2 = detect_surface2(df)
        #print(f"Profile: {name}, Detected Surface (snowmicropyn): {surface2} mm")

        plot_surface(df, name, surface)