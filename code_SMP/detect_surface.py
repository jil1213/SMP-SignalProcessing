import numpy as np
import matplotlib.pyplot as plt

from snowmicropyn import Profile
from snowmicropyn.tools import smooth
#from code_SMP.readSMP import load_all_smp_profiles

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
    numerator = window_size * sum_xy - sum_x * sum_y
    denominator = window_size * sum_x2 - sum_x ** 2
    slope = numerator / denominator

    # Pad result to original length with NaNs on both sides for 
    pad = (len(x) - len(slope)) // 2
    result = np.full_like(x, np.nan)
    result[pad:pad+len(slope)] = slope

    return result


def detect_surface(df, name):
    """
    Detects the snow surface in an SMP profile by identifying the first 
    significant gradient increase in the force signal.
    1. Computes gradient of force using a moving linear regression and smoothing
    2. Calculates a threshold based on the standard deviation of the gradient
    3. Identifies the first point where the gradient exceeds the threshold
       With checking the next 1mm for a stable surface value

    Parameters:
        df (pd.DataFrame): Profile with 'distance' and 'force' columns
        name (str): Profile name for debugging

    Returns:
        surface (float): Surface position
        grad (np.ndarray): Smoothed force gradient
        threshold (float): Gradient threshold used for detection
    """
    distance = df["distance"]
    force = df["force"]
    window_len = 242 # thats 1mm/resolution of SMP 


    # 1. Compute gradient with moving linear regression over 1mm window
    grad = moving_linear_regression(distance, force, window_mm=1.0)

    # smoothing with hanning
    grad = smooth(grad, window_len)
    grad = grad[:len(distance)]  #cut to length of distance


    # 2. Calculate threshold based on standard deviation of the gradient
    # method: take STD of the gradient from the air measurement without disturbances, form threshold out of it
    # assumption I: the air measurement can be found in the first 10cm of the profile
    # assumption II: to get a stable std a a value range of 10mm is used for the calculation -> window

    max_distance_mm = 100.0      # assumption I: scan first 100mm (10cm) as possible air measurement
    window = int(20 / 0.00413223123177886) # assumption II: 10mm window size to calculate std air (length_mm/resolution)

    # Initialize variables before loop
    min_std = np.inf
    air_std = None
    air_mean = None

    grad_air = grad[distance <= (distance[0] + max_distance_mm)]
    for i in range(len(grad_air) - window + 1):
        window_grad = grad_air[i : i + window]
        s = window_grad.std()
        if s < min_std:
            min_std = s
            air_std = s
            air_mean = window_grad.mean()

    threshold = 5 * air_std #with air_mean + 5* air_std a very small bit worse - snowmicropyn method


    # 3. Find first significant gradient rise above threshold = surface
    surface = None
    for i in range(1000, len(grad)): # Start at index 1000 to avoid noise at the very top (in snowmicropyn:100)
        if grad[i] > threshold:
            # Check if next 1mm after the surface value is not air again
            check_window = grad[i+1 : i+1+window_len]
            if np.sum(check_window < threshold) / len(check_window) >= threshold:
                 continue
            surface = distance[i]
            break

    # Fallback if no surface can be found
    if surface is None:
        print(f"[{name}] No valid surface detected using new method.")
        surface = distance[0] 

    return surface, grad, threshold


def detect_surface_snowmicropyn(file):
    #compare with snowmicropyn package detection method
    smp_profile = Profile.load(file)
    surface = Profile.detect_surface(smp_profile)
    return surface



def plot_surface(df, name, surface, surface2): 
    plt.figure(figsize=(8, 5))
    plt.plot(df["distance"], df["force"])
    plt.axvline(x=surface, color='red', linestyle='--', label=f'Surface lin reg: {surface} mm')
    plt.axvline(x=surface2, color='blue', linestyle='--', label=f'Surface snowmicropyn: {surface2} mm')
    #plt.yscale('log')
    plt.xlabel("Distance (mm)")
    plt.ylabel("Force (N)")
    plt.title(f"Surface detection Profile: {name}")
    plt.grid()
    plt.legend()
    plt.show()

#this kind of comment to avoid circular import 
"""""
if __name__ == "__main__":
    #smp_profiles = load_all_smp_profiles(pnt=True)
    for name, df in smp_profiles.items():
        surface = detect_surface(df, name)
        print(f"Profile: {name}, Detected Surface1: {surface} mm")
        #works only with Profile (not with df)
        file = 'data/smp_profiles/'+name+'.PNT' #load origin file to use with snowmicropyn package 
        surface2 = detect_surface_snowmicropyn(file)
        print(f"Profile: {name}, Detected Surface2: {surface2} mm")

        plot_surface(df, name, surface, surface2)
"""""