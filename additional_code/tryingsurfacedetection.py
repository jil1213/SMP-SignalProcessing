# code to try out surface detection on other profiles 
# visualizations of detected surface 
import matplotlib.pyplot as plt
import numpy as np
import configparser

from pathlib import Path
from snowmicropyn import Profile
from sklearn.metrics import mean_absolute_error,  mean_squared_error
from code_SMP.detect_surface import detect_surface

def compute_metrics(surface_ini_all, surface_old_all, surface_new_all, folder_path): 
        # MAE - Mean Absolute Error
        mae_old = mean_absolute_error(surface_ini_all, surface_old_all)
        mae_new = mean_absolute_error(surface_ini_all, surface_new_all)

        # MSE - Mean Squared Error
        mse_old = mean_squared_error(surface_ini_all, surface_old_all)
        mse_new = mean_squared_error(surface_ini_all, surface_new_all)

        # RMSE - Root Mean Squared Error
        rmse_old = np.sqrt(mse_old)
        rmse_new = np.sqrt(mse_new)

        # Create formatted text instead of array (for later use in .txt file)
        scores = (
        f"MAE old - new: {mae_old:.2f} - {mae_new:.2f}\n"
        f"MSE old - new: {mse_old:.2f} - {mse_new:.2f} mm^2\n"
        f"RMSEold - new: {rmse_old:.2f} - {rmse_new:.2f} mm\n")

        return scores

def append_run_information(info_text, scores, target_file=Path("additional_code/test_data3/run_summary.txt")):

    content = f"\n\n--------------------------------------\n{info_text}\nScores:\n{scores}\n"

    # Check if info_text already exists in file
    if target_file.exists():
        with target_file.open("r", encoding="utf-8") as f:
            existing_content = f.read()
        if info_text in existing_content:
            print("Information is already saved in file. Nothing appended.")
            return
    # Append content
    with target_file.open("a", encoding="utf-8") as f:
        f.write(content)

    print(f"Information successfully appended to {target_file}")


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
        plt.savefig(folder_path / f"surface_{profile_name}.png")
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

        # Calculate delta errors for each profile
        delta_old = surface_old_all - surface_ini_all
        delta_new = surface_new_all - surface_ini_all

        #compute error metrics
        scores = compute_metrics(surface_ini_all, surface_old_all, surface_new_all, folder_path)

        # Change here for different parameter runs
        info_text = (f"NEW METRICS: Run with moving linear regression and threshold finding with\n air_std over rolling window 10mm\n threshold = 7*air_std\n")

        # Append information to the run_summary.txt
        append_run_information(info_text, scores)

        # Plotting deviations
        plt.figure(figsize=(10, 5))
        plt.plot(delta_old, label="Old vs Ini", marker='.')
        plt.plot(delta_new, label="New vs Ini", marker='.')
        # Dummy handle for text explanation
        plt.plot([], [], ' ',label="Note:\nNegative values mean surface is detected earlier\nthan in manually ini file.\n delta = surface - surface_ini")
        plt.xlabel("Profile Index")
        plt.ylabel("Deviation (mm)")
        plt.title("Deviation from Ground Truth (surface_ini)")
        plt.legend()
        plt.grid()
        plt.tight_layout()
        plt.savefig(folder_path / f"delta_error.png")

        # Zoomed plotting deviations for better focus on small values
        plt.figure(figsize=(10, 5))
        plt.plot(delta_old, label="Old vs Ini", marker='.')
        plt.plot(delta_new, label="New vs Ini", marker='.')
        # Dummy handle for text explanation
        plt.plot([], [], ' ',label="Note:\nNegative values mean surface is detected earlier\nthan in manually ini file.\n delta = surface - surface_ini")
        plt.xlabel("Profile Index")
        plt.ylabel("Deviation (mm)")
        plt.title("Zoomed Deviation from Ground Truth (surface_ini)")
        plt.ylim(-25, 25) #zoomed range but looses some profiles with high error
        plt.legend()
        plt.grid()
        plt.tight_layout()
        plt.savefig(folder_path / f"delta_error_zoomed.png")
