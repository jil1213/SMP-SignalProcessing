# code to try out surface detection on other profiles 
# visualizations of detected surface 
from skimage.filters import threshold_otsu
from scipy.ndimage import uniform_filter1d
import matplotlib.pyplot as plt
import numpy as np
import configparser

from snowmicropyn import Profile
from pathlib import Path
from code_SMP.detect_surface import detect_surface, moving_linear_regression

def detect_surface2(df, name, plot=False): 
        distance = df["distance"]
        force = df["force"]

        # gradient over window with 1mm 
        grad = moving_linear_regression(distance, force, window_mm=1.0)

        # Threshold 
        # method: make dynamic threshold with otsu 
        grad = grad[~np.isnan(grad)] #make sure there are no NaNs
        threshold = threshold_otsu(grad) #way to big -> mabe not working for this case? 

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

def detect_surface3(df, name, plot=False,
                               initial_range=5000, check_window=10000, mad_thresh=3):
    distance = df["distance"].values
    force = df["force"].values

    # Step 1: calculate gradient (moving linear regression)
    grad = moving_linear_regression(distance, force, window_mm=1)
    

    # Step 2: define robust threshold from initial range (ignores short peaks)
    grad_initial = grad[:initial_range]
    grad_initial_clean = grad_initial[~np.isnan(grad_initial)]
    
    # robust threshold: median + 3 * MAD (Median Absolute Deviation)
    median = np.median(grad_initial_clean)
    mad = np.median(np.abs(grad_initial_clean - median))
    #threshold = median + mad_thresh * mad
    threshold = 0.004
    # Step 3: search for persistent gradient rise
    surface = None
    for i in range(initial_range, len(grad) - check_window):
        if grad[i] > threshold:
            # check if gradient remains high in following window
            window_values = grad[i:i+check_window]
            if np.mean(window_values[~np.isnan(window_values)]) > threshold:
                surface = distance[i]
                break

    return surface

def detect_surface4(df, name, plot=False,
                              grad_window_mm=1.0,
                              baseline_range=5000,
                              persist_window=200,
                              threshold_factor=4):
    distance = df["distance"].values
    force = df["force"].values

    # Step 1: Gradient (1mm Fenster mit moving linear regression)
    grad = moving_linear_regression(distance, force, window_mm=grad_window_mm)
    grad = np.nan_to_num(grad)

    # Step 2: Rolling variance ("Rausch-Level" – analog RM+HOS VAD)
    smooth_power = uniform_filter1d(grad ** 2, size=100)
    baseline = smooth_power[:baseline_range]
    baseline_mean = np.median(baseline)
    threshold = baseline_mean * threshold_factor

    # Step 3: Zustandserkennung – Sprachanalog: Surface = Sprache
    surface = None
    for i in range(baseline_range, len(grad) - persist_window):
        window = smooth_power[i:i + persist_window]
        if np.mean(window) > threshold:
            surface = distance[i]
            break
    return surface

# import all SMP profiles existing in the folder (getting names out of )
folder_path = Path("additional_code/test_data3")
smp_profiles = {}
#pnt_files = folder_path.glob("*.PNT")
pnt_files = folder_path.rglob("*.PNT") # for recurcsive search in subfolders for test_data3
for file in pnt_files:
        if folder_path == Path("additional_code/test_data3"):
                ini_file = file.with_suffix(".ini") # get corresponing ini
                config = configparser.ConfigParser()
                config.read(ini_file)

                # only keep profiles with qa_flag == 1
                try:
                        qa_flag = int(config["quality assurance"].get("qa_flag", 0))
                except (KeyError, ValueError):
                        qa_flag = 0

                if qa_flag != 1:
                        continue

                # get surface from ini
                try:
                        surface_ini = float(config["markers"]["surface"])
                except (KeyError, ValueError):
                        surface_ini = None

        smp_profile = Profile.load(file)
        profile_name = smp_profile.name
        df = smp_profile.samples

        # get surface with old method 
        surface_old = Profile.detect_surface(smp_profile)
        #print(f"Profile: {profile_name}, Detected Surface (old method): {surface_old} mm")
        # get surface with new method
        surface_new = detect_surface(df, profile_name)
        #print(f"Profile: {profile_name}, Detected Surface (new method): {surface_new} mm")
        # get surface with otsu threshold: not working right now 
        # surface_otsu = detect_surface2(df, profile_name, plot=False)
        # get surface with new method 3 
        surface3 = detect_surface3(df, profile_name, plot=False)
        # get surface in vad (VOice acitvity detectuion style)
        surface4 = detect_surface4(df, profile_name, plot=False)
        # define plot window: min und max der beiden surfaces ±1 cm
        x_min = min(surface_old, surface_new) - 10  # mm
        x_max = max(surface_old, surface_new) + 10  # mm
        # filter data in the plot range for autoscaling y-axis
        df_plot = df[(df["distance"] >= x_min) & (df["distance"] <= x_max)]
        y_min = df_plot["force"].min()
        y_max = df_plot["force"].max()

        #plot surfaces in range of both 
        plt.figure(figsize=(8, 5))
        plt.plot(df["distance"], df["force"], label="Force Profile")
        plt.axvline(x=surface_old, color='red', linestyle='--', label=f'Surface (old method): {surface_old} mm')
        plt.axvline(x=surface_new, color='blue', linestyle='--', label=f'Surface (new method): {surface_new} mm')
        if surface_ini is not None:
            plt.axvline(x=surface_ini, color='green', linestyle='--', label=f'Surface (from ini): {surface_ini} mm')
        # plt.axvline(x=surface_otsu, color='orange', linestyle='--', label=f'Surface (Otsu method): {surface_otsu} mm')
        plt.axvline(x=surface3, color='purple', linestyle='--', label=f'Surface (new method 3): {surface3} mm')
        plt.axvline(x=surface4, color='cyan', linestyle='--', label=f'Surface (VAD method): {surface4} mm')
        plt.xlabel("Distance (mm)")
        plt.ylabel("Force (N)")
        plt.title(f"Surface Detection for Profile: {profile_name}")
        plt.grid()
        plt.legend()
        plt.xlim(x_min, x_max)
        plt.ylim(y_min - 1, y_max + 1)
        plt.savefig(folder_path / f"surface_{profile_name}.png")
        plt.close()