# code to evaluate surface detection for all profiles
from snowmicropyn import Profile
from pathlib import Path
import configparser
import pandas as pd
from code_SMP.detect_surface import detect_surface

def calculate_surfaces(folder_path):
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
    output_file = root / "SMP-SignalProcessing" / "surfacedetection_evaluate" / "surface_detection_cache.csv"

    # Calculate and save results
    results = calculate_surfaces(folder_path)
    save_surface_results_to_csv(results, output_file)
