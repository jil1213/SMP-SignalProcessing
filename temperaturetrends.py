import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path 
from readSMP import plot_profiles, load_all_smp_profiles
from plot_interpolate import interpolate
from plotSMP import bulid_pairs, plot_pairs

def compare_temperature_trends(smp_profiles): 

    # build velocitiy pairs
    paired_profiles = bulid_pairs(smp_profiles)
    for df8, name8, df20, name20 in paired_profiles:

        # Interpolate
        df_drift8 = interpolate(name8, df8, save=True)
        df_drift20 = interpolate(name20, df20, save=True)

        # Interpolation trend
        coeffs8 = np.polyfit(df_drift8["distance"], df_drift8["force"], deg=1)
        trendline8 = np.polyval(coeffs8, df_drift8["distance"])
        df_trend8 = pd.DataFrame({"distance": df_drift8["distance"],"force": trendline8})
        coeffs20 = np.polyfit(df_drift20["distance"], df_drift20["force"], deg=1)
        trendline20 = np.polyval(coeffs20, df_drift20["distance"])
        df_trend20 = pd.DataFrame({"distance": df_drift20["distance"],"force": trendline20})

        #Plot both: Interpolation and trend of each velocity
        plt.figure(figsize=(8, 5))
        plt.plot(df_drift8["distance"], df_drift8["force"], label=f"{name8} (v=8 mm/s)", color='tab:orange')
        plt.plot(df_drift20["distance"], df_drift20["force"], label=f"{name20} (v=20 mm/s)", color='tab:blue')
        plt.plot(df_drift8["distance"], trendline8, '--', label=f"Trend {name8}", color='tab:orange')
        plt.plot(df_drift20["distance"], trendline20, '--', label=f"Trend {name20}", color='tab:blue')

        plt.xlabel("Distance (mm)")
        plt.ylabel("Force (N)")
        plt.title(f"Interpolated & Trendline: {name8} vs {name20}")
        plt.legend()
        plt.grid()

        filename = f"comparison_trend_{name8}_vs_{name20}"
        target_dir = Path("output/trend")
        plt.savefig((target_dir / filename).with_suffix(".png"))
        plt.close()

        #plot only trends 
        filename = f"trend_{name8}_vs_{name20}"
        title = f"Trend {name8} vs {name20}"
        target_dir = Path("output/trend")
        plot_pairs([(df_trend8, name8, df_trend20, name20)], filename=filename, save=True, title=title, target_dir=target_dir)


def extract_temperature_trends(smp_profiles, save=False): 
    # build velocitiy pairs
    paired_profiles = bulid_pairs(smp_profiles)
    for df8, name8, df20, name20 in paired_profiles:

        # Interpolate
        df_drift8 = interpolate(name8, df8, save=True)
        df_drift20 = interpolate(name20, df20, save=True)

        #Create Difference
        min_len = min(len(df_drift8), len(df_drift20))
        distance = df_drift20["distance"].values[:min_len] 
        diff_force = df_drift8["force"].values[:min_len]  - df_drift20["force"].values[:min_len] 

        # Create Trend of diff
        coeffs = np.polyfit(distance, diff_force, deg=1)
        trendline = np.polyval(coeffs, diff_force)

        plt.figure(figsize=(8, 5))
        plt.plot(distance, diff_force, label=f"{name8} - {name20}")
        plt.plot(distance, trendline, '--', label=f"Trend {name8} - {name20}")
        plt.xlabel("Distance (mm)")
        plt.ylabel("Force Difference (N)")
        plt.title(f"Interpolated Drift Difference: {name8} - {name20}")
        plt.legend()
        plt.grid()
        filename = f"diff_interpolation_{name8}_vs_{name20}"
        target_dir = Path("output/trend")

        if save == True: 
            # save as figure png
            plt.savefig((target_dir / filename).with_suffix(".png"))
            #save as pdf for better quality in another folder
            (target_dir / "pdf").mkdir(parents=True, exist_ok=True)
            plt.savefig((target_dir / "pdf" / filename).with_suffix(".pdf"), format="pdf", bbox_inches="tight")
        else:
            plt.show()
    return diff_force


if __name__ == "__main__":
    #load from csv for aligned profiles
    smp_profiles = load_all_smp_profiles(pnt=False)
    #compare_temperature_trends(smp_profiles)
    extract_temperature_trends(smp_profiles, save=True)