import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from code_SMP.readSMP import load_all_smp_profiles
from code_json.readjson import load_lawis_profile

def align_SMP_to_Snowprofile(df):
    # get day to knwo which profile to align 
    if df.attrs["date"] == 1: 
        #align to first Snowprofile
        json, boundaries = load_lawis_profile("data/LawisProfile23044.json")
    elif df.attrs["date"] == 2:
        #align to second Snowprofile
        json, boundaries = load_lawis_profile("data/LawisProfile23778.json")

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
    plt.show()

if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles(pnt=True)
    for name, df in smp_profiles.items():
        align_SMP_to_Snowprofile(df) 