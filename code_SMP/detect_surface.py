import matplotlib.pyplot as plt
import numpy as np
from skimage.filters import threshold_otsu
from snowmicropyn import Profile
from snowmicropyn.tools import smooth
#from code_SMP.readSMP import load_all_smp_profiles
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

    # Pad result to original length with NaNs on both sides for 
    pad = (len(x) - len(slope)) // 2
    result = np.full_like(x, np.nan)
    result[pad:pad+len(slope)] = slope

    return result


def detect_surface(df, name):
    distance = df["distance"]
    force = df["force"]

    # gradient with linear regression over 1mm window
    grad = moving_linear_regression(distance, force, window_mm=1.0)
    # nans to zero
    grad = np.nan_to_num(grad, nan=0.0)
    #smoothing with hanning, same as smooth() of snowmicropyn
    grad = smooth(grad, 242)
    window_len = 242 # thats 1mm/resolution of SMP 
    #s = np.r_[grad[window_len - 1:0:-1], grad, grad[-1:-window_len:-1]]
    #w = eval('np.' + 'hanning' + '(window_len)')
    #grad = np.convolve(w / w.sum(), s, mode='valid')

    # Threshold 
    # method: take STD of the 1st to 2nd cm -maybe try smaller range a bit earlier
    # assumption I: the first two mm are always an air measurement
    # assumption II: 1st mm is excluded in order to ignore the starting and possible disturbances
    #early_std = np.nanstd(grad[2500:5000])
    #New method to find air std
    # Parameters for rolling window
    window_length_mm = 10.0  # length of rolling window in mm
    max_scan_mm = 100.0      # scan only first 100mm (10cm) of measurement
    resolution = 0.00413223123177886

    window_size = int(window_length_mm / resolution)

    # Initialize variables to track lowest std
    min_std = np.inf
    best_std = None

    # Loop over indices in the first 10cm
    for start_idx in range(0, len(grad) - window_size):
        if distance[start_idx] > (distance[0] + max_scan_mm):
            break
        window_grad = grad[start_idx : start_idx + window_size]
        s = np.std(window_grad)
        if s < min_std:
            min_std = s
            best_std = s

    # Use the smallest std found in any 1cm window in the first 10cm
    early_std = best_std

    threshold = 5 * early_std

    surface = None 

    # Find first significant gradient rise above threshold
    for i in range(1000, len(grad)): #in snowmicropyn 100 but makes higher error here
        if grad[i] > threshold:
            check_window = grad[i+1 : i+1+window_len] # calculate gradient for 1mm after possible surface value

            if np.sum(check_window < threshold) / len(check_window) >= threshold: #make a different threshold here
                 continue
            surface = distance[i]
            break

    # fallback when no surface can be found
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