import matplotlib.pyplot as plt

from code_SMP.readSMP import load_all_smp_profiles
from code_visualizations.plot_interpolate import interpolate

# detrend smp profiles with calculated drift 

if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()
    
    for name, df in smp_profiles.items():
        # find trend
        df_drift = interpolate(name, df, plot=False, save=False)

        # substract trend from original force 
        force_detrended = df["force"].values - df_drift["force"].values
        df["force_detrended"] = force_detrended #detrending kann lead to negative values 

        #to avoid negatives: add negative value as offset to profile
        offset = force_detrended.min()
        df["force_detrended"] += abs(offset)

        # plot both drifts together 
        plt.figure(figsize=(8, 5))
        #plt.plot(df["distance"], df["force"], label="normal")
        plt.plot(df["distance"], df["force_detrended"], label="detrended")
        plt.xlabel("Distance (mm)")
        plt.ylabel("Force (N)")
        plt.title(f"Detrended {name}")
        plt.legend()
        plt.grid()
        plt.savefig(f"output/detrending/{name}_detrended.png")
        plt.close()