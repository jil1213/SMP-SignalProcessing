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
    #plot both dfs together
    fig, ax = plt.subplots(figsize=(10, 6))
    # Plot SMP data
    ax.plot(df["distance"], df["force"], label="SMP Hardness", color='blue')
    # Plot JSON data
    ax.plot(json["distance"], json["hardness_id"], label="JSON Hardness", color='orange', marker='x')
    # Set labels and title
    ax.set_xlabel("Distance from surface (mm)")
    ax.set_ylabel("Hardness (Index)")
    ax.set_title("SMP vs JSON Hardness Profile")
    ax.legend()
    ax.grid()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles(pnt=True)
    for name, df in smp_profiles.items():
        align_SMP_to_Snowprofile(df) 