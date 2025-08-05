import matplotlib.pyplot as plt
from pathlib import Path

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
        alpha = 1.0 if label == "Mean" else 0.6
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