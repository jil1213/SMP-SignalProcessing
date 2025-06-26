# code to try out surface detection on other profiles 
# visualizations of detected surface 
from skimage.filters import threshold_otsu
from scipy.ndimage import uniform_filter1d
import matplotlib.pyplot as plt
import numpy as np
import configparser
from sklearn.metrics import mean_absolute_error, mean_squared_error

from snowmicropyn import Profile
from pathlib import Path
from code_SMP.detect_surface import detect_surface, moving_linear_regression

# import all SMP profiles existing in the folder (getting names out of )
folder_path = Path("additional_code/test_data3")
smp_profiles = {}
pnt_files = folder_path.rglob("*.PNT") # for recurcsive search in subfolders for test_data3

# prepare arrays for plotting later 
surface_ini_all = []
surface_old_all = []
surface_new_all = []
profile_names = []
thresholds = []

for file in pnt_files:
        surface_ini = None
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

        # get surface with new method
        surface_new, grad, threshold = detect_surface(df, profile_name)

        # define plot window: min und max der beiden surfaces ±1 cm
        x_min = min(surface_old, surface_new) - 10  # mm
        x_max = max(surface_old, surface_new) + 10  # mm
        # filter data in the plot range for autoscaling y-axis
        df_plot = df[(df["distance"] >= x_min) & (df["distance"] <= x_max)]
        y_min = df_plot["force"].min()
        y_max = df_plot["force"].max()

        #plot surfaces in range of both 
        # plot only profiles where surface ini and new have a big distance
        #if surface_ini - surface_new > 5 or surface_new - surface_ini > 5: 
        plt.figure(figsize=(8, 5))
        #plt.plot(df["distance"], grad[:len(df)], label="Force Profile")
        plt.plot(df["distance"], df["force"], label="Force Profile")
        plt.axvline(x=surface_old, color='red', linestyle='--', label=f'Surface (old method): {surface_old} mm')
        plt.axvline(x=surface_new, color='blue', linestyle='--', label=f'Surface (new method): {surface_new} mm')
        if surface_ini is not None:
                plt.axvline(x=surface_ini, color='green', linestyle='--', label=f'Surface (from ini): {surface_ini} mm')
        plt.xlabel("Distance (mm)")
        plt.ylabel("Force (N)")
        plt.title(f"Surface Detection for Profile: {profile_name}, threshold: {threshold:.4f}")
        plt.grid()
        plt.legend()
        plt.xlim(x_min, x_max)
        plt.ylim(y_min - 1, y_max + 1)
        #plt.savefig(folder_path / f"surface_{profile_name}.png")
        #plt.show()
        plt.close()

        #fill array for error calculations later
        surface_ini_all.append(surface_ini)
        surface_old_all.append(surface_old)
        surface_new_all.append(surface_new)
        profile_names.append(profile_name)
        thresholds.append(threshold)


if surface_ini is not None: 
        # convert to numpy arraay for calculations
        surface_ini_all = np.array(surface_ini_all)
        surface_old_all = np.array(surface_old_all)
        surface_new_all = np.array(surface_new_all)
        thresholds = np.array(thresholds)

        # Fehler berechnen
        delta_old = np.abs(surface_old_all - surface_ini_all)
        delta_new = np.abs(surface_new_all - surface_ini_all)


        # calculate median of errors
        median_old = np.median(delta_old)
        median_new = np.median(delta_new)
        print(f"Median absolute deviation (old method): {median_old:.2f} mm")
        print(f"Median absolute deviation (new method): {median_new:.2f} mm")
        
        #calculate mean 
        mae_new = mean_absolute_error(surface_ini_all, surface_new_all)
        mae_old = mean_absolute_error(surface_ini_all, surface_old_all)
        rmse_new = mean_squared_error(surface_ini_all, surface_new_all, squared=False)
        rmse_old = mean_squared_error(surface_ini_all, surface_old_all, squared=False)
        print(f"Mean Absolute Error (old method): {mae_old:.2f} mm")
        print(f"Mean Absolute Error (new method): {mae_new:.2f} mm")
        print(f"Root Mean Squared Error (old method): {rmse_old:.2f} mm")
        print(f"Root Mean Squared Error (new method): {rmse_new:.2f} mm")

        # Linienplot pro Profil
        plt.figure(figsize=(10, 5))
        plt.plot(delta_old, label="Old vs Ini", marker='.')
        plt.plot(delta_new, label="New vs Ini", marker='.')
        plt.xlabel("Profile Index")
        plt.ylabel("Absolute Deviation (mm)")
        plt.title("Deviation from Ground Truth (surface_ini)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(folder_path / f"delta_error.png")
