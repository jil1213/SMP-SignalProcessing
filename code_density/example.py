# file to test some stuff

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

from scipy import signal
from code_SMP.readSMP import load_all_smp_profiles, load_pnt


df, profile_name, spatial_resolution = load_pnt("data/smp_profiles/S45M1056.PNT")

forces = df["force"].to_numpy()

#detrending 
k1 = np.mean(forces)
# signal detrending as suggested by Proksch 2015
force_detrended = signal.detrend(forces-k1, type='linear')

#functions out of snowmicropyn package
def chunkup(samples, window, overlap):
    """Combine data into chunks.

    :param samples: SMP samples
    :param window: size of moving window in mm
    :param overlap: overlap factor in percent
    """
    if not 0 <= overlap < 100:
        raise ValueError('overlap value {} invalid, must be a value >= 0 and < 100 [%]'.format(overlap))

    first = samples.distance.iloc[0] if not samples.empty else 0
    last = samples.distance.iloc[-1] if not samples.empty else 0

    step = window - (window * overlap / 100)
    center = first
    chunks = []
    while center < last:
        # Calculate where block begins and ends
        begin = center - window / 2.
        end = center + window / 2.

        # Filter for samples with a block and add it to the list of
        # blocks along with its center (the blocks center distance)
        within = np.logical_and(samples.distance >= begin, samples.distance < end)
        chunk_samples = samples[within]
        chunks.append((center, chunk_samples))

        center = center + step
    return chunks

#: Default value for SnowMicroPen's cone diameter im mm.
SMP_CONE_DIAMETER = 5  # [mm]
#: Default value for SnowMicroPen's projected cone area, depends on :const:`SMP_CONE_DIAMETER`.
SMP_CONE_AREA = (SMP_CONE_DIAMETER / 2.) ** 2 * math.pi  # [mm^2]

def calc_step(spatial_res, forces, cone_area=SMP_CONE_AREA):
    """Calculate shot noise parameters for a segment of a profile.

    This is the actual implementation of the algorithm described in the
    publication and calculates the derived parameters for a single segment of
    the profile.

    :param spatial_res: Spatial resolution of profile.
    :param forces: Iterable containing the force values.
    :param cone_area: Projected area of cone (tip) of SnowMicroPen in square
           millimeters.
    :return: A tuple containing lambda, f0, delta and L.
    """
    n = len(forces)

    # Mean and variance of force signal
    k1 = np.mean(forces)
    k2 = np.var(forces)

    # signal detrending as suggested by Proksch 2015
    force_detrended = signal.detrend(forces-k1, type='linear')

    # Covariance/Autocorrelation (Equation 8 in publication)
    c_f = np.correlate(force_detrended, force_detrended, mode='full')

    # Equation 11 in publication
    delta = -(3. / 2) * c_f[n - 1] / (c_f[n] - c_f[n - 1]) * spatial_res

    # Equation 12 in publication
    try: # Try/catch for speed
        lambda_ = (4. / 3) * (k1 ** 2) / k2 / delta  # Intensity
    except FloatingPointError:
        lambda_ = np.inf # A warning will be shown later
    f0 = (3. / 2) * k2 / k1

    # According to equation 2 in publication
    L = (cone_area / lambda_) ** (1. / 3)

    return lambda_, f0, delta, L


def calc(samples, window, overlap):

    # Calculate spatial resolution of the distance samples as median of all
    # step sizes.
    spatial_res = np.median(np.diff(samples.distance.values))

    # Split dataframe into chunks
    chunks = chunkup(samples, window, overlap)
    result = []
    with np.errstate(divide='raise'): # Allow for our own handling with all np configurations
        for center, chunk in chunks:
            f_median = np.median(chunk.force)
            sn = calc_step(spatial_res, chunk.force)
            result.append((center, f_median) + sn)
    result = pd.DataFrame(result, columns=['distance', 'force_median', 'L2012_lambda', 'L2012_f0',
                                         'L2012_delta', 'L2012_L'])
    if np.isinf(result.L2012_lambda).values.any(): # check only once in the end
        print("Error inf")
    return result

result = calc(df, window=1, overlap=50) #Proksch Window size 2.5

# Kalman filter implementation -not finetuned yet
def apply_kalman_filter(signal, process_variance=1e-5, measurement_variance=0.1):
    """
    Simple 1D Kalman filter for a single variable.
    :param signal: Input force signal
    :param process_variance: Variance of the process (Q)
    :param measurement_variance: Variance of the measurement noise (R)
    """
    n = len(signal)
    x_hat = np.zeros(n)         # estimated signal
    P = np.zeros(n)             # estimate error
    x_hat[0] = signal[0]        # initial estimate
    P[0] = 1.0                  # initial estimate covariance

    Q = process_variance        # process noise covariance
    R = measurement_variance    # measurement noise covariance

    for k in range(1, n):
        # Prediction step
        x_hat_minus = x_hat[k-1]
        P_minus = P[k-1] + Q

        # Update step
        K = P_minus / (P_minus + R)
        x_hat[k] = x_hat_minus + K * (signal[k] - x_hat_minus)
        P[k] = (1 - K) * P_minus

    return x_hat

# Apply Kalman filter to the raw force signal
forces_kalman = apply_kalman_filter(forces)

# Plot
plt.figure(figsize=(8, 5))
#plt.plot(df["distance"], df["force"], label=profile_name)
#plt.plot(df["distance"], force_detrended, label="Detrended Force", linestyle='--')
plt.plot(result["distance"], result["force_median"], label="Median Force", linestyle='--')
#plt.plot(df["distance"], forces_kalman, label="Kalman Filtered Force", linestyle='--', color='green')
plt.xlabel("Distance (mm)")
plt.ylabel("Force (N)")
plt.title(f"{profile_name} Profile")
plt.legend()
plt.grid()
plt.show()
