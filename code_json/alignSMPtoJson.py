import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from snowmicropyn import Profile
from code_SMP.readSMP import load_all_smp_profiles
from code_json.readjson import load_lawis_profile, plot_lawis_hardness

def align_SMP_to_Snowprofile(df):
    # get day to knwo which profile to align 
    if df.attrs["date"] == 1: 
        #align to first Snowprofile
        json = load_lawis_profile("data/LawisProfile23044.json")
    elif df.attrs["date"] == 2:
        #align to second Snowprofile
        json = load_lawis_profile("data/LawisProfile23778.json")

    # Plot SMP together with JSON profile
    fig, ax = plt.subplots(figsize=(8, 5))

    # plot first grain colors as colored bands
    for i in range(0, len(json), 2):
        left = json.iloc[i + 1]["distance"]
        right = json.iloc[i]["distance"]
        color = json.iloc[i]["color"]
        ax.fill_betweenx([df["force"].min(), df["force"].max()], left, right, color=color)

    #plot SMP force
    ax.plot(df["distance"], df["force"], label="SMP Force")
    ax.set_ylabel("Force (N)")

    # create second y axis 
    ax2 = ax.twinx()
    # plot Hardness Index of JSON profile
    ax2.plot(json["distance"], json["hardness_id"], color='black', linestyle='--', label="Hardness Index")
    ax2.set_ylabel("Hardness Index")

    ax.grid()
    ax.set_xlabel("Distance from surface (mm)")
    ax.set_title(f"{name} aligned to manual profile day {df.attrs['date']}")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles(pnt=True)
    for name, df in smp_profiles.items():
        align_SMP_to_Snowprofile(df) 