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

def detect_surface3(profile):
    #compare with snowmicropyn package detection method
    surface2 = profile.detect_surface()

    return surface2


def downsample(x, n=2):
    if n < 1:
        raise ValueError('n must be bigger or equal 1')

    i = np.mod(len(x), n)
    x = x[:len(x) - i].reshape(-1, n).mean(axis=1)
    return x

def smooth(x, window_len=11, window='hanning'):
    """Smooth the data using a window with requested size"""

    if x.ndim != 1:
        raise ValueError('Function only accepts 1 dimension arrays.')
    if x.size < window_len:
        raise ValueError('Input vector needs to be bigger than window size.')
    if window_len < 3:
        return x
    valid = ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']
    if window not in valid:
        raise ValueError('Invalid value for parameter window. Valid values: ' + ','.join(valid))

    s = np.r_[x[window_len - 1:0:-1], x, x[-1:-window_len:-1]]

    if window == 'flat':
        # moving average
        w = np.ones(window_len, 'd')
    else:
        w = eval('np.' + window + '(window_len)')

    y = np.convolve(w / w.sum(), s, mode='valid')
    return y

def detect_surface2(df):
    """Automatic detection of surface (begin of snowpack).

    :param profile: The profile to detect surface in.
    :return: Distance where surface was detected.
    :rtype: float
    """

    # Cut off ca. 1 mm
    distance = df["distance"]
    distance = distance.values[250:]
    force = df["force"]
    force = force.values[250:]

    force = downsample(force, 20)
    distance = downsample(distance, 20)

    force = smooth(force, 242)

    y_grad = np.gradient(force)
    y_grad = downsample(y_grad, 3)
    x_grad = downsample(distance, 3)

    max_force = np.amax(force)

    for i in np.arange(100, x_grad.size):
        std = np.std(y_grad[:i - 1])
        mean = np.mean(y_grad[:i - 1])
        if y_grad[i] >= 5 * std + mean:
            surface = x_grad[i]
            break

    if i == x_grad.size - 1:
        surface = max_force

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

if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles(pnt=True)
    for name, df in smp_profiles.items():
        surface = detect_surface(df, name)
        print(f"Profile: {name}, Detected Surface1: {surface} mm")
        #does not work yet because you need snowmicropyn profile
        surface2 = detect_surface2(df)
        print(f"Profile: {name}, Detected Surface2: {surface2} mm")
        
        plot_surface(df, name, surface, surface2)