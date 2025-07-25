import matplotlib.pyplot as plt
from pathlib import Path

from snowmicropyn import loewe2012
from snowmicropyn.parameterizations.calonne_richter2020 import CalonneRichter2020
from code_automated_correlation.automated_processing import load_profiles


def calculate_density_profile(df, window=1, overlap=50): #i think this values are default but not sure, check again
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
        delta=loewe_results["L2012_delta"].values
    )

    # Create density profile DataFrame
    df_density = loewe_results[["distance"]].copy()
    df_density["density"] = densities

    return df_density

def plot_density(df_density, name, save=True, target_dir=Path("output/density_profiles")):
    """
    Plot density profile.
    """
    plt.figure(figsize=(8, 5))
    plt.plot(df_density["distance"],df_density["density"])
    plt.xlabel("Distance (mm)")
    plt.ylabel("Density (kg/m³)")
    plt.title(f"Density Profile: {name}")
    plt.gca()
    plt.grid(True)

    if save:
        target_dir.mkdir(parents=True, exist_ok=True)
        plt.savefig(target_dir / f"density_profile_{name}.png")
    else:
        plt.show()
    plt.close()

if __name__ == "__main__":
    # Load all profiles from all days (means all folders)
    # Use data 
    root = Path(__file__).resolve().parent 
    input_root = root.parent/ "code_automated_correlation" / "raw_data" 
    output_root = root / "output" / "density_single"


    for folder_path in sorted(input_root.iterdir()):
        if folder_path.is_dir():
            day = folder_path.name
            print(f"Processing {day}")
            smp_profiles = load_profiles(folder_path)

        for name, df in smp_profiles.items():
            print(f"Processing: {name}")
            try:
                df_density = calculate_density_profile(df, window=1, overlap=50)
                plot_density(df_density, name, target_dir=output_root)
            except Exception as e:
                print(f"Error processing {name}: {e}")
