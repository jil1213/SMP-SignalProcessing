import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import xml.etree.ElementTree as ET

from snowmicropyn import loewe2012
from snowmicropyn.parameterizations.calonne_richter2020 import CalonneRichter2020
from code_automated_correlation.c_automated_grouping import analyze_day
from code_automated_correlation.d_automated_mean import compute_aligned_mean
plt.style.use(r'c:/Users/jille/Documents/Uni/Master-Mechatronik/Masterarbeit/SMP-SignalProcessing/latex_default.mplstyle')


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
    plt.figure(figsize=(5.5, 3.5))
    for df, label in zip(dfs_densities, labels):
        alpha = 1.0 if label == "Mean" or "Manual density measurement" or "SnowPro" or "DensityCutter" else 0.6
        plt.plot(df["distance"], df["density"], label=label, alpha=alpha)
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

            label = f"Manual density measurement"
            manual_dfs.append((df, label))


    # .xlsx Files (SnowPro and DensityCutter)
    for file in input_path.glob("*.xlsx"):
        if file.stem.startswith(day):
            suffix = file.stem[len(day):].lstrip("-_").lower()  # get what's after day name (day eg.20250321-densitycutter)
            df_raw = pd.read_excel(file)

            if "snowdepth" in df_raw.columns and "mean" in df_raw.columns:
                df_raw = df_raw[["snowdepth", "mean"]]
                bottoms = df_raw["snowdepth"].values * 10  # convert to mm
                tops = [0] + list(bottoms[:-1])
                densities = df_raw["mean"].values

                distance_steps = []
                density_steps = []

                for top, bottom, dens in zip(tops, bottoms, densities):
                    if pd.isna(dens):
                        continue  #Step over Nan layers
                    distance_steps.extend([top, bottom])
                    density_steps.extend([dens, dens])

                # Create DataFrame and convert to numeric (handle "NaN" strings)
                df = pd.DataFrame({"distance": distance_steps, "density": pd.to_numeric(density_steps, errors="coerce")})

                # Optional: add surface point if first density is valid
                if not pd.isna(df["density"].iloc[0]):
                    df = pd.concat([
                        pd.DataFrame({"distance": [0.0], "density": [df["density"].iloc[0]]}),
                        df
                    ], ignore_index=True)

                # convert coloumns to float, if not convertable, set to NaN
                df["density"] = pd.to_numeric(df["density"], errors="coerce")

                label = "SnowPro" if "snowpro" in suffix else "DensityCutter"
                manual_dfs.append((df, label))

    return manual_dfs if manual_dfs else None



if __name__ == "__main__":

    root = Path(__file__).resolve().parent 
    input_root = root.parent/ "code_automated_correlation" / "raw_data" 
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
            rem_densities = [calculate_density_profile(smp_profiles[name], name) for name in remaining]

            # Plot all individual and mean
            plot_density([ref_density] + rem_densities + [mean_density], [ref_name] + remaining + ["Mean"],
                filename=f"density_global_group_{ref_name}", save=True, target_dir=day_output_dir)


        # Manual density measurements
        manual_results = load_manual_density(day, input_root)

        if manual_results is not None:
            dfs = [mean_density] + [df for df, _ in manual_results]
            labels = ["Mean"] + [label for _, label in manual_results]

            plot_density(dfs, labels, filename=f"density_mean_manual_{day}", target_dir=day_output_dir)