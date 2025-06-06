import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from code_SMP.readSMP import load_all_smp_profiles
from code_json.readjson import load_lawis_profile
from code_visualizations.plot_mean import calc_mean

def correct_height(df, angle):
    df["distance"] = df["distance"]/ np.cos(np.deg2rad(angle))
    return df

def align_SMP_to_Snowprofile(df, name, std=None):
    # get day to know which profile to align 
    if df.attrs["date"] == 1: 
        #align to first Snowprofile
        json, boundaries, angle = load_lawis_profile("data/LawisProfile23044.json")
    elif df.attrs["date"] == 2:
        #align to second Snowprofile
        json, boundaries, angle = load_lawis_profile("data/LawisProfile23778.json")

    # adapt height of SMP to match the JSON (angle correction)
    df = correct_height(df, angle)
    #print(f"Max height after correction {name}: ", df["distance"].max())

    # Plot SMP together with JSON profile !!ATTENTION!! plot has fixed height for force (7) 
    fig, ax = plt.subplots(figsize=(8, 5))

    #plot SMP force
    ax.plot(df["distance"], df["force"], label="SMP Force")
    ax.set_ylabel("Force (N)")
    ax.set_ylim(0, 7) # max fix y axis for better comparison

    # plot first grain colors as colored bands
    current_color = json["color"].iloc[0]
    start = json["distance"].iloc[0]

    for i in range(1, len(json)):
        color = json["color"].iloc[i]
        if color != current_color or i == len(json) - 1:
            end = json["distance"].iloc[i]
            ax.fill_betweenx([0, 7], start, end, color=current_color) #!Fixed height y axis
            start = end
            current_color = color

    #plot std if available (when plotting mean)
    if std is not None:
        ax.fill_between(df["distance"],
                        df["force"] - std,
                        df["force"] + std,
                        alpha=0.5,
                        label="±1 SD")

    # Plot boundaries as vertical lines with 80% transparency
    for boundary in boundaries["distance"]:
        ax.axvline(x=boundary, color='black', linestyle=':', linewidth=0.8, alpha=0.5, zorder=5)

    # create second y axis
    ax2 = ax.twinx()
    # plot Hardness Index of JSON profile
    ax2.plot(json["distance"], json["hardness_id"], color='black', linestyle='--', linewidth=0.8, alpha=0.5, label="Hardness Index")
    ax2.set_ylabel("Hardness Index")
    ax2.set_ylim(bottom=0)

    ax2.grid()
    ax2.legend()
    ax.set_xlabel("Distance from surface (mm)")
    ax.set_title(f"{name} and manual profile day {df.attrs['date']}")
    plt.tight_layout()
    #plt.show()

    #save plot
    # save as figure png
    target_dir = Path("output/SMPtoJson")
    plt.savefig((target_dir / f"{name}toJson").with_suffix(".png"))
    #save as pdf for better quality in another folder
    #(target_dir / "pdf").mkdir(parents=True, exist_ok=True)
    #plt.savefig((target_dir / "pdf" / f"{name}toJson").with_suffix(".pdf"), format="pdf", bbox_inches="tight")

    plt.close()

def align_mean_to_Snowprofile(all_mean_profiles): 
    for date in [1, 2]:
        for velocity in [8, 20]:
            df_data = all_mean_profiles[date][velocity]
            #changing column name from mean to force for easy handling
            df = pd.DataFrame({
                "distance": df_data["distance"],
                "force": df_data["mean"]
            })
            df.attrs["date"] = date
            name = f"Mean_Day_{date}_Veloc_{velocity}"
            std = df_data["std"]
            align_SMP_to_Snowprofile(df, name, std)


if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles(pnt=True)
    for name, df in smp_profiles.items():
        align_SMP_to_Snowprofile(df, name) 

    # Align mean to Snowprofile
    # use buffered csv profiles aligned to first
    smp_profiles = load_all_smp_profiles(pnt=False, aligned="first")
    all_mean_profiles = calc_mean(smp_profiles, save=True)
    align_mean_to_Snowprofile(all_mean_profiles)