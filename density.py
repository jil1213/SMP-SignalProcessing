import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import xml.etree.ElementTree as ET

from snowmicropyn import loewe2012
from snowmicropyn.parameterizations.calonne_richter2020 import CalonneRichter2020
from c_automated_grouping import analyze_day
from d_automated_mean import compute_aligned_mean


def calculate_density_profile(df, profile_name, window=1, overlap=0): #i think this values are default but not sure, check again
    """
    Compute density profile using loewe2012 + CalonneRichter2020 model.
    
    :param df: DataFrame with columns 'distance' and 'force'
    :param window: Moving window size in mm
    :param overlap: Overlap percentage between windows
    :return: DataFrame with 'distance' and 'density' columns
    """

    # Calculate shot noise parameters from loewe2012
    loewe_results = loewe2012.calc(df, window, overlap)

    # Calculate density using CalonneRichter2020 model
    densities = CalonneRichter2020().density(
        F_m=loewe_results["force_median"].values,
        LL=loewe_results["L2012_L"].values,
        lamb=loewe_results["L2012_lambda"].values,
        f0=loewe_results["L2012_f0"].values,
        delta=loewe_results["L2012_delta"].values)

    # Create density profile DataFrame
    df_density = loewe_results[["distance"]].copy()
    df_density["density"] = densities

    return df_density

def plot_density(dfs_densities, labels, filename, save=True, target_dir=Path("output/density_profiles")):
    min_len = len(dfs_densities[labels.index("Mean")])
    plt.figure(figsize=(5.5, 3.5))
    for df, label in zip(dfs_densities, labels):
        if label == "Manual density measurement":
            plt.plot(df["distance"][:min_len], df["density"][:min_len], label=label, alpha=1.0)
        elif label == "Mean":
            plt.plot(df["distance"], df["density"], label=label, alpha=1.0, color="tab:red")
        else:
            plt.plot(df["distance"][:min_len], df["density"][:min_len], label=label, alpha=0.6)
    plt.xlabel("Distance (mm)")
    plt.ylabel("Density (kg/m³)")
    plt.legend(fontsize="small")
    plt.grid()
    plt.tight_layout()

    if save:
        target_dir.mkdir(parents=True, exist_ok=True)
        plt.savefig(target_dir / f"{filename}.svg")
    else:
        plt.show()
    plt.close()



def load_manual_density(day, input_path):
    manual_dfs = []
    # .xml SnowProfile File
    for file in input_path.glob("*.xml"):
        if file.stem.startswith(day):
            tree = ET.parse(file)
            root = tree.getroot()
            ns = {"caaml": "http://caaml.org/Schemas/SnowProfileIACS/v6.0.3"}
            layers = root.findall(".//caaml:densityProfile/caaml:Layer", ns)

            #slope angle 
            angle = float(root.find(".//caaml:validSlopeAngle/caaml:SlopeAnglePosition/caaml:position", ns).text) #data["location"]["slope_angle"]

            thicknesses = []
            densities = []

            for layer in layers:
                thickness = float(layer.find("caaml:thickness", ns).text)
                density = float(layer.find("caaml:density", ns).text)
                thicknesses.append(thickness)
                densities.append(density)

            # Calculate upper and lower bounds for each layer in mm
            bottoms = pd.Series(thicknesses).cumsum() * 10
            tops = bottoms - pd.Series(thicknesses) * 10

            distance_steps = []
            density_steps = []

            for top, bottom, dens in zip(tops, bottoms, densities):
                distance_steps.extend([top, bottom])
                density_steps.extend([dens, dens])

            # Add surface level
            distance_steps.insert(0, 0.0)
            density_steps.insert(0, densities[0])

            df = pd.DataFrame({"distance": distance_steps, "density": density_steps})
            # correct distance with slope angle 
            df["distance"] = df["distance"]/ np.cos(np.deg2rad(angle))

            label = f"Manual density measurement"
            manual_dfs.append((df, label))


    # .xlsx Files (SnowPro and DensityCutter)
    for file in input_path.glob("*.xlsx"):
        if file.stem.startswith(day):
            suffix = file.stem[len(day):].lstrip("-_").lower()  # get what's after day name (day eg.20250321-densitycutter)
            df_raw = pd.read_excel(file)
            if day == "20250131": # Not valid for other profiles right now!
                angle = 25
            elif day == "20250321": 
                angle= 21 

            # decide for what range values are valid 
            if suffix == "snowpro":
                range = 40 / np.cos(np.deg2rad(angle)) #mm in both directions (/is angle correction)
                label = f"SnowPro sensor"
                df_raw = df_raw[["snowdepth", "mean"]]
                distances = (df_raw["snowdepth"].values * 10) / np.cos(np.deg2rad(angle)) # convert to mm and correct with slope angle correction
                densities = df_raw["mean"].values
                df = pd.DataFrame({"distance": distances, "density": densities})
                manual_dfs.append((df, label))

            elif suffix == "densitycutter":
                range = 20 / np.cos(np.deg2rad(angle))
                label = f"Manual method with cylindrical sampling device"
                df_raw = df_raw[["snowdepth", "mean"]]
                distances = (df_raw["snowdepth"].values * 10) / np.cos(np.deg2rad(angle)) # convert to mm and correct with slope angle correction
                densities = df_raw["mean"].values
                df = pd.DataFrame({"distance": distances, "density": densities})
                manual_dfs.append((df, label))

    return manual_dfs if manual_dfs else None



if __name__ == "__main__":

    root = Path(__file__).resolve().parent 
    input_root = root.parent/ "raw_data" 
    output_root = root / "output" / "density"

    for folder_path in sorted(input_root.iterdir()):
        if not folder_path.is_dir():
            continue

        result = analyze_day(folder_path)

        day = result["day"]
        print(f"Processing {day}")
        smp_profiles = result["smp_profiles"]
        ref_result = result["reference_result"]
        pairs = result["pairs"]
        groups = result["groups"]

        day_output_dir = output_root / day
        day_output_dir.mkdir(parents=True, exist_ok=True)


        # Density for all pairs
        for ref_name, remaining, score in pairs:
            mean_df, _ = compute_aligned_mean(smp_profiles, (ref_name, [remaining], score))
            mean_df = mean_df[["distance", "mean_force"]].rename(columns={"mean_force": "force"})

            ref_density = calculate_density_profile(smp_profiles[ref_name], ref_name)
            rem_density = calculate_density_profile(smp_profiles[remaining], remaining)
            mean_density = calculate_density_profile(mean_df, "Mean")

            plot_density([ref_density, rem_density, mean_density], [ref_name, remaining, "Mean"], 
                filename=f"density_pair_{ref_name}_{remaining}", save=True, target_dir=day_output_dir)

        # Density for global group (best group in full day)
        ref_name, remaining, score = ref_result
        if ref_name is not None:
            mean_df, _ = compute_aligned_mean(smp_profiles, (ref_name, remaining, score))
            mean_df = mean_df[["distance", "mean_force"]].rename(columns={"mean_force": "force"})

            ref_density = calculate_density_profile(smp_profiles[ref_name], ref_name)
            mean_density = calculate_density_profile(mean_df, "Mean")
            #print mean density in command line
            print("Mean density SMP derived:", mean_density["density"].mean())
            rem_densities = [calculate_density_profile(smp_profiles[name], name) for name in remaining]

            # Plot all individual and mean
            plot_density([ref_density] + rem_densities + [mean_density], [ref_name] + remaining + ["Mean"],
                filename=f"density_global_group_{ref_name}", save=True, target_dir=day_output_dir)


        # Manual density measurements
        manual_results = load_manual_density(day, input_root)

        if manual_results is not None:
            #dfs = [mean_density] + [df for df, _ in manual_results]
            #labels = ["Mean"] + [label for _, label in manual_results]

            plt.figure(figsize=(5.5, 3.5))
            plt.plot(mean_density["distance"], mean_density["density"], label="Mean", alpha=1.0)
            # Plot manual datasets depending on label
            for df, label in manual_results:
                if label == "SnowPro sensor":
                    x = df["distance"].values
                    y = df["density"].values
                    xerr = np.full_like(x, 40.0)
                    plt.errorbar(x, y, xerr=xerr, fmt='o', label=label, color='tab:orange',
                         alpha=0.7, markersize=2, capsize=0.5, linewidth=1)
                elif label == "Manual method with cylindrical sampling device":
                    x = df["distance"].values
                    y = df["density"].values
                    # 34 mm links, 0 mm rechts
                    xerr = [np.full_like(x, 34.0), np.zeros_like(x)]
                    plt.errorbar(x, y, xerr=xerr, fmt='o', label=label, color='tab:green',
                         alpha=0.7, markersize=2, capsize=0.5, linewidth=1)                
                elif label == "Manual density measurement":
                    plt.plot(df["distance"], df["density"], label=label)
            plt.xlabel("Distance (mm)")
            plt.ylabel("Density (kg/m³)")
            plt.legend(fontsize="small")
            plt.grid()
            plt.tight_layout()
            filename=f"density_mean_manual_{day}"
            plt.savefig(day_output_dir / f"{filename}.svg")
            plt.close()