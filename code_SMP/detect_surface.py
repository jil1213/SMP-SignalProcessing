import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from snowmicropyn import Profile
from code_SMP.readSMP import load_all_smp_profiles
import numpy as np

def moving_linear_regression(x, y, window_mm=1.0):
    # calculate window size 
    # fix resolution of SMP
    resolution = 0.00413223123177886 #mm
    window_size = int(window_mm / resolution)

    # convert data to numpy arrays for save convolution
    x = np.asarray(x)
    y = np.asarray(y)

    # Precompute moving sums
    ones = np.ones(window_size)

    sum_x = np.convolve(x, ones, mode='valid')
    sum_y = np.convolve(y, ones, mode='valid')
    sum_xy = np.convolve(x * y, ones, mode='valid')
    sum_x2 = np.convolve(x * x, ones, mode='valid')

    # use linear regression formula to calculate slope
    n = window_size
    numerator = n * sum_xy - sum_x * sum_y
    denominator = n * sum_x2 - sum_x ** 2
    slope = numerator / denominator

    # Pad result to original length with NaNs on both sides 
    pad = (len(x) - len(slope)) // 2
    result = np.full_like(x, np.nan)
    result[pad:pad+len(slope)] = slope

    return result


def detect_surface(df, name, plot=False):
    distance = df["distance"]
    force = df["force"]

    # calculate gradient - very exact uses two points and calculates slope
    #gradient = np.gradient(log_force, log_distance)

    # gradient over window with 1mm 
    #grad = moving_linear_regression(log_distance, log_force, window_mm=1.0)
    grad = moving_linear_regression(distance, force, window_mm=1.0)

    # Threshold 
    #method 1: take STD of the 1st to 2nd mm 
    early_std = np.nanstd(grad[2500:5000])
    threshold = 5 * early_std

    # method 2: take mean --not that good than m1
    #early_mean = np.nanmedian(np.abs(grad[2500:5000]))
    #threshold = max(early_mean * 5, 0.02)  # if noise almost 0 take 0.02

    # Find first significant gradient rise above threshold
    for i in range(len(grad)):
        if grad[i] > threshold:
            surface = distance[i]
            break
    if plot == True: 
        #plot gradient 
        plt.figure(figsize=(8, 5))
        plt.plot(distance, grad, label='Moving Derivative (1mm window)', linestyle='--')
        plt.axvline(x=surface, color='red', linestyle='--', label=f'Surface: {surface} mm')
        plt.xlabel("Distance (mm)")
        plt.ylabel("Gradient of log force")
        plt.title(f"Gradient of log force vs Distance {name}")
        plt.grid()
        plt.legend()
        plt.show()

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
        surface = detect_surface(df, name)
        print(f"Profile: {name}, Detected Surface: {surface} mm")
        #does not work yet because you need snowmicropyn profile
        #surface2 = detect_surface2(df)
        #print(f"Profile: {name}, Detected Surface (snowmicropyn): {surface2} mm")

        #plot_surface(df, name, surface)