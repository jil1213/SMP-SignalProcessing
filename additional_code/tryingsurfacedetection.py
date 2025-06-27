# code to try out surface detection on other profiles 
# visualizations of detected surface 
import matplotlib.pyplot as plt
import numpy as np
import configparser

from pathlib import Path
from snowmicropyn import Profile
from sklearn.metrics import mean_absolute_error,  mean_squared_error
from code_SMP.detect_surface import detect_surface


def append_run_information(info_text, scores, target_file=Path("additional_code/test_data3/run_summary.txt")):

    content = f"\n\n--------------------------------------\n\{info_text}\nScores:\n{scores}\n"

    # Check if info_text already exists in file
    if target_file.exists():
        with target_file.open("r", encoding="utf-8") as f:
            existing_content = f.read()
        if info_text in existing_content:
            print("Information is already savedin file. Nothing appended.")
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

        # Calculate delta errors for each profile
        delta_old = np.abs(surface_old_all - surface_ini_all)
        delta_new = np.abs(surface_new_all - surface_ini_all)

        # Calculate median
        median_old = np.median(delta_old)
        median_new = np.median(delta_new)

        # Calculate mean 
        mae_new = mean_absolute_error(surface_ini_all, surface_new_all)
        mae_old = mean_absolute_error(surface_ini_all, surface_old_all)
        rmse_new = mean_squared_error(surface_ini_all, surface_new_all, squared=False)
        rmse_old = mean_squared_error(surface_ini_all, surface_old_all, squared=False)

        # Change here for different parameter runs
        info_text = (f"Run with moving linear regression and threshold finding with\n early_std over rolling window 1mm\n threshold = 5 * early_std\n")

        # Input scores
        scores = (
        f"Median old - new: {median_old:.2f} - {median_new:.2f} mm\n"
        f"Mean Absolute Error old - new: {mae_old:.2f} - {mae_new:.2f} mm\n"
        f"RMSE old - new: {rmse_old:.2f} - {rmse_new:.2f} mm")

        # Append information to the run_summary.txt
        append_run_information(info_text, scores)

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
