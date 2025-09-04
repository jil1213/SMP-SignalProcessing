# code to evaluate surface detection for all profiles
from snowmicropyn import Profile
from pathlib import Path
import configparser
import pandas as pd
from code_SMP.detect_surface import detect_surface
from surfacedetection_tuning.tune_surfacedetection import compute_metrics, plot_delta_error

# for plotting master thesis only
import numpy as np
import matplotlib.pyplot as plt
plt.style.use(r'c:/Users/jille/Documents/Uni/Master-Mechatronik/Masterarbeit/SMP-SignalProcessing/latex_default.mplstyle')


def load_surface_data(csv_path):
    """
    Loads surface detection results from CSV and returns arrays for evaluation.
    """
    df = pd.read_csv(csv_path)
    surface_ini_all = df["surface_ini"].dropna().values
    surface_old_all = df.loc[df["surface_ini"].notna(), "surface_old"].values
    surface_new_all = df.loc[df["surface_ini"].notna(), "surface_new"].values
    profile_names = df.loc[df["surface_ini"].notna(), "profile_name"].values
    return surface_ini_all, surface_old_all, surface_new_all, profile_names


def calculate_surfaces(folder_path, output_path):
    """
    Loops over all .PNT files in folder_path and extracts surface positions.
    Returns a list of dictionaries with metadata and surface positions.
    """
    pnt_files = folder_path.rglob("*.PNT")
    results = []

    for file in pnt_files:
        surface_ini = None
        ini_file = file.with_suffix(".ini")  # get corresponding ini file
        config = configparser.ConfigParser()
        config.read(ini_file)

        # Only use profiles with qa_flag == 1
        try:
            qa_flag = int(config["quality assurance"].get("qa_flag", 0))
        except (KeyError, ValueError):
            qa_flag = 0

        if qa_flag != 1:
            continue

        # Get surface from ini file
        try:
            surface_ini = float(config["markers"]["surface"])
        except (KeyError, ValueError):
            surface_ini = None

        smp_profile = Profile.load(file)
        profile_name = smp_profile.name
        df = smp_profile.samples

        # Get surface positions
        surface_old = Profile.detect_surface(smp_profile)
        surface_new, grad, threshold = detect_surface(df, profile_name)
        
        # Plotting Outliers (only for master thesis)-------
        if surface_ini is not None:
            delta_new = abs(surface_new - surface_ini)
            if (delta_new > 100):
                plt.figure(figsize=(5.5, 3.5))
                plt.plot(df["distance"], df["force"])
                plt.xlabel("Distance (mm)")
                plt.ylabel("Force (N)")
                # Vertical lines at reference and detected surfaces
                plt.axvline(surface_ini, color="k", linestyle="--", label=f"reference surface = {surface_ini:.1f} mm")
                plt.axvline(surface_old, color="tab:orange", linestyle="-.", label=f"surface existing method = {surface_old:.1f} mm")
                plt.axvline(surface_new, color="tab:green", linestyle="-.", label=f"surface new method = {surface_new:.1f} mm")
                plt.grid()
                plt.legend()
                plt.tight_layout()
                #plt.show()
                plt.savefig(output_path / f"outliers/outlier_{profile_name}.svg")  # for master thesis vector graphic

                # Zoomed range for all 
                plt.figure(figsize=(5.5, 3.5))
                plt.plot(df["distance"], df["force"])
                plt.xlabel("Distance (mm)")
                plt.xlim(-2, 220)
                plt.ylim(-0.1, 0.3)
                plt.ylabel("Force (N)")
                # Vertical lines at reference and detected surfaces
                plt.axvline(surface_ini, color="k", linestyle="--", label=f"reference surface = {surface_ini:.1f} mm")
                plt.axvline(surface_old, color="tab:orange", linestyle="-.", label=f"surface existing method = {surface_old:.1f} mm")
                plt.axvline(surface_new, color="tab:green", linestyle="-.", label=f"surface new method = {surface_new:.1f} mm")
                plt.grid()
                plt.legend()
                plt.tight_layout()
                #plt.show()
                plt.savefig(output_path  / f"outliers/zoomed_outlier_{profile_name}.svg")  # for master thesis vector graphic
        #--------------------------------------------------

        # Append result to list
        results.append({
            "folder": file.parent.name,
            "profile_name": profile_name,
            "surface_ini": surface_ini,
            "surface_old": surface_old,
            "surface_new": surface_new
        })

    return results


def save_surface_results_to_csv(results, output_file):
    """
    Saves a list of surface detection results to a CSV file.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_file, index=False)
    print(f"Surface detection results saved to: {output_file}")


if __name__ == "__main__":
    # Define input and output paths
    root = Path(__file__).resolve().parent.parent.parent
    folder_path = root / "raw_data"
    output_path = root / "SMP-SignalProcessing" / "surfacedetection_evaluate"
    csv_file = output_path / "surface_detection_cache.csv"
    output_file = output_path / "surface_detection_cache.csv"

    # Calculate and save results
    results = calculate_surfaces(folder_path, output_path)
    save_surface_results_to_csv(results, output_file)
    
    # Load data and compute metrics
    surface_ini_all, surface_old_all, surface_new_all, profile_names = load_surface_data(csv_file)
    scores = compute_metrics(surface_ini_all, surface_old_all, surface_new_all)

    print("Evaluation scores:", scores)
    
    # Plot delta errors
    plot_delta_error(surface_ini_all, surface_old_all, surface_new_all, output_path)
