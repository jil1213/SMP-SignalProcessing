# code to try out surface detection on other profiles 
# visualizations of detected surface 

import matplotlib.pyplot as plt
import numpy as np

from snowmicropyn import Profile
from pathlib import Path
from code_SMP.detect_surface import detect_surface

# import all SMP profiles existing in the folder (getting names out of )
folder_path = Path("additional_code/test_data")
smp_profiles = {}
pnt_files = folder_path.glob("*.PNT")
for file in pnt_files:
        smp_profile = Profile.load(file)
        profile_name = smp_profile.name
        df = smp_profile.samples

        # get surface with old method 
        surface_old = Profile.detect_surface(smp_profile)
        #print(f"Profile: {profile_name}, Detected Surface (old method): {surface_old} mm")
        # get surface with new method
        surface_new = detect_surface(df, profile_name)
        #print(f"Profile: {profile_name}, Detected Surface (new method): {surface_new} mm")
        
        # define plot window: min und max der beiden surfaces ±1 cm
        x_min = min(surface_old, surface_new) - 10  # mm
        x_max = max(surface_old, surface_new) + 10  # mm
        # filter data in the plot range for autoscaling y-axis
        df_plot = df[(df["distance"] >= x_min) & (df["distance"] <= x_max)]
        y_min = df_plot["force"].min()
        y_max = df_plot["force"].max()
        
        #plot surfaces in range of both 
        plt.figure(figsize=(8, 5))
        plt.plot(df["distance"], df["force"], label="Force Profile")
        plt.axvline(x=surface_old, color='red', linestyle='--', label=f'Surface (old method): {surface_old} mm')
        plt.axvline(x=surface_new, color='blue', linestyle='--', label=f'Surface (new method): {surface_new} mm')
        plt.xlabel("Distance (mm)")
        plt.ylabel("Force (N)")
        plt.title(f"Surface Detection for Profile: {profile_name}")
        plt.grid()
        plt.legend()
        plt.xlim(x_min, x_max)
        plt.ylim(y_min - 1, y_max + 1)
        plt.savefig(folder_path / f"{profile_name}_surface.png")
        plt.close()