import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
from readSMP import load_all_smp_profiles
from plotSMP import bulid_pairs, plot_pairs

target_dir = Path("output/cross_correlations")

#method to get the offset of two profiles by crosscorrelation
def get_offset(df1, df2, name1, name2, plot=False):
    """Calculate the offset between two profiles using cross-correlation."""

    #Cut dfs to apply autocorrelation - only use for offset method!
    start = 50000
    end = 200000 #150.000 values

    #check if array is long enough, if not: take a smaller range
    if len(df2) < end:
        print(f"Profile is too short, using smaller range for cross-correlation.")
        print(len(df2))
        start = 10000
        end = 50000

    df1_cut = df1.iloc[start:end]
    df2_cut = df2.iloc[start:end]

    # mean centering to get a more exact correlation
    #df1_cut["force"] = df1_cut["force"].values - np.mean(df1_cut["force"])
    #df2_cut["force"] = df2_cut["force"].values - np.mean(df2_cut["force"])

    #low-pass filter to get a more exact correlation
    #...

    # Calculate cross-correlation to cutted dfs
    correlation = np.correlate(df1_cut["force"], df2_cut["force"], mode='full')

    dx = np.mean(np.diff(df1_cut["distance"]))  # mean spacing in mm

    index_shifts = np.arange(-len(df1_cut["force"]) + 1, len(df1_cut["force"]))       # create array of right size, starting from -n+1 to n
    index_shifts_mm = index_shifts * dx #convert lags into distances in mm

    lag_max = np.argmax(correlation) - (len(df1_cut["force"]) - 1) #lag with max correlation
    offset_mm = lag_max * dx #distance offset

    #Print results
    print(f"Crosscorrelation {name1} - {name2}")
    print(f"Max corr: {np.max(correlation)}")
    print(f"Offset: {offset_mm:.2f} mm (lag: {lag_max})")
    if plot == True:
        plt.figure(figsize=(8, 4))
        plt.plot(index_shifts_mm, correlation)
        plt.title(f"Cross-Correlation over distance {name1} & {name2}")
        plt.xlabel("Distance (mm)")
        plt.ylabel("Correlation")
        plt.grid(True)
        #plt.show()
        plt.savefig(target_dir / f"corr_{name1}_{name2}.png")

    return offset_mm, correlation, lag_max


def align_profiles(smp_profiles, pairs=True, plot=False, save=False): 
    #case only pairs to compare
    if pairs == True:
        paired_profiles = bulid_pairs(smp_profiles)
        for df1, name1, df2, name2 in paired_profiles:
            offset_mm, correlation, lag = get_offset(df1, df2, name1, name2)
            df2_shifted = df2.copy()
            #shift indices of df2 with lag to get max correlation --arrays get cut in the end (last part missing)
            #positive lag shift to right side - negative lag shift to left side
            df2_shifted['force'] = df2_shifted['force'].shift(lag, fill_value=0)
            if plot == True:
                title = f"Signal shifted with cross-Correlation {name1} & {name2}"
                plot_pairs([(df1, name1, df2_shifted, name2)], target_dir,title)

            # update/save in original dictionary
            smp_profiles[name2] = df2_shifted
        #save correlation results as csv
        if save == True:
            smp_profiles_shifted = smp_profiles.copy()
            save_dir = Path("data/aligned_pairs")
            save_dir.mkdir(parents=True, exist_ok=True)
            for name, df in smp_profiles.items():
                df.to_csv(save_dir / f"{name}_aligned.csv", index=False)


    #case more than two profiles to compare
    else:
        # Get the first non-temperature-profile as reference
        reference_name = next((name for name, df in smp_profiles.items() if df.attrs.get("velocity", 0) != 0), None)
        if reference_name is None:
            raise ValueError("Kein gültiges Referenzprofil gefunden (alle velocity == 0).")

        reference_df = smp_profiles[reference_name]
        profile_names = list(smp_profiles.keys())

        for name in profile_names[0:]:
            df = smp_profiles[name]
            offset_mm, correlation, lag = get_offset(reference_df, df, reference_name, name)
            #shifted ro reference
            df_shifted = df.copy()
            df_shifted['force'] = df_shifted['force'].shift(lag, fill_value=0)

            #cut to same length as reference
            if len(df_shifted) < len(reference_df):
                padding_len = len(reference_df) - len(df_shifted)
                padding = pd.DataFrame({
                    'force': [0] * padding_len,
                    'distance': [np.nan] * padding_len
                })
                df_shifted = pd.concat([df_shifted[['force']], padding], ignore_index=True)
                df_shifted['distance'] = reference_df['distance'].values[:len(reference_df)]
            elif len(df_shifted) > len(reference_df):
                df_shifted = df_shifted.iloc[:len(reference_df)]
                df_shifted['distance'] = reference_df['distance'].values[:len(reference_df)]
            else:
                df_shifted['distance'] = reference_df['distance'].values

            if plot==True:
                title = f"Aligned: {name} to {reference_name}"
                plot_pairs([(reference_df, reference_name, df_shifted, name)],
                        filename=f"aligned_{name}_to_{reference_name}",
                        title=title,
                        save=True,
                        target_dir=target_dir)

            smp_profiles[name] = df_shifted  # update original

        #save correlation results as csv
        if save == True:
            smp_profiles_shifted = smp_profiles.copy()
            save_dir = Path("data/aligned_first")
            save_dir.mkdir(parents=True, exist_ok=True)
            for name, df in smp_profiles.items():
                df.to_csv(save_dir / f"{name}_aligned.csv", index=False)

    smp_profiles_shifted = smp_profiles.copy()
    return smp_profiles_shifted


if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()
    #to aligning two profiles
    smp_profiles_shifted = align_profiles(smp_profiles, pairs=True, save=False)
    #to align all profiles to the first one
    smp_profiles_shifted = align_profiles(smp_profiles, pairs=False, save=False)