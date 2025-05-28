import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
from readSMP import load_all_smp_profiles
from plotSMP import bulid_pairs, plot_pairs

target_dir = Path("output/cross_correlations")

#method to get the offset of two profiles by crosscorrelation
def get_offset(df1, df2, name1, name2, plot=True):
    """Calculate the offset between two profiles using cross-correlation."""

    #Cut dfs to apply autocorrelation - only use for offset method!
    start = 50000
    end = 220000 #170.000 values

    #make shorter Array for day 2 (so ground peaks get cut off)
    if len(df2) < 250000: 
        start = 50000
        end = 200000 #170.000 values

    #check if array is long enough, if not: take a smaller range
    if len(df2) < end:
        print(f"Profile is too short, using smaller range for cross-correlation.")
        print(len(df2))
        start = 10000
        end = 50000

    df1_cut = df1.iloc[start:end]
    df2_cut = df2.iloc[start:end]

    # Calculate cross-correlation to cutted dfs
    correlation = np.correlate(df1_cut["force"], df2_cut["force"], mode='full')

    dx = np.mean(np.diff(df1_cut["distance"]))  # mean spacing in mm

    index_shifts = np.arange(-len(df1_cut["force"]) + 1, len(df1_cut["force"]))       # create array of right size, starting from -n+1 to n
    index_shifts_mm = index_shifts * dx #convert lags into distances in mm

    # Lag with max correlation 
    # lag_max = np.argmax(correlation) - (len(df1_cut["force"]) - 1) #lag with max correlation global
    # local max  around center (most realistic)
    start, end = len(correlation) // 2 - 20000, len(correlation) // 2 + 20000
    lag_local = np.argmax(correlation[start:end])
    lag_max = (start + lag_local) - (len(df1_cut["force"]) - 1)

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
        plt.close()

    return offset_mm, correlation, lag_max


def align_profiles(smp_profiles, pairs=True, plot=True, save=False): 
    #case only pairs to compare
    if pairs == True:
        paired_profiles = bulid_pairs(smp_profiles)
        for df1, name1, df2, name2 in paired_profiles:
            offset_mm, correlation, lag = get_offset(df1, df2, name1, name2)
            df2_shifted = df2.copy()
            # shift indices of df2 with lag to get max correlation
            # positive lag shift to right side - negative lag shift to left side
            df2_shifted['force'] = df2_shifted['force'].shift(lag, fill_value=np.nan)

            # bring both to same length
            min_len = min(len(df1), len(df2_shifted))
            df1 = df1.iloc[:min_len]
            df2_shifted = df2_shifted.iloc[:min_len]

            # cut both profiles to common length
            # find valid Index range
            force1_valid = ~df1["force"].isna() #boolean for all values if value=True, if Nan=False
            force2_valid = ~df2_shifted["force"].isna()
            valid_mask = force1_valid & force2_valid #find valid range (as long as boolean=True)
            valid_index = df1.index[valid_mask] #get index of valid range

            #cut to valid range
            df1_shifted = df1.loc[valid_index].reset_index(drop=True)
            df2_shifted = df2_shifted.loc[valid_index].reset_index(drop=True)

            #take distance values from df1 for both dfs
            df2_shifted["distance"] = df1_shifted["distance"]

            if plot == True:
                title = f"Signal shifted with cross-Correlation {name1} & {name2}"
                filename = f"aligned_{name1}_to_{name2}"
                plot_pairs([(df1_shifted, name1, df2_shifted, name2)], filename, save=True, title=title, target_dir=target_dir)

            # update/save in original dictionary
            smp_profiles[name1] = df1_shifted
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
     for day in [1,2]:
        # take all profiles of one day 
        day_profiles = {name: df for name, df in smp_profiles.items()
                        if df.attrs.get("date") == day and df.attrs.get("velocity", 0) != 0}

        # Get the first non-temperature-profile of the day as reference
        reference_name = next(iter(day_profiles))
        reference_df = day_profiles[reference_name]

        # create dict for aligned dfs for later 
        aligned_profiles = {}
        aligned_profiles[reference_name] = reference_df.copy()
        lag_dict = {}

        for name, df in day_profiles.items():
            #except the reference profile
            if name == reference_name:
                continue
            df = smp_profiles[name]
            offset_mm, correlation, lag = get_offset(reference_df, df, reference_name, name)
            # shift to reference
            df_shifted = df.copy()
            df_shifted['force'] = df_shifted['force'].shift(lag, fill_value=np.nan)

            aligned_profiles[name] = df_shifted
            lag_dict[name] = lag

        # update reference_df to match min_len
        min_len = min(len(df) for df in aligned_profiles.values())
        for name in aligned_profiles:
            aligned_profiles[name] = aligned_profiles[name].iloc[:min_len].reset_index(drop=True)

        reference_df = aligned_profiles[reference_name]
        # reference distance beginning with zero
        reference_distance = reference_df["distance"] - reference_df["distance"].iloc[0]
        reference_df["distance"] = reference_distance.reset_index(drop=True)
        aligned_profiles[reference_name] = reference_df.reset_index(drop=True)


        # search valid range for all profiles of one day
        masks = [~df["force"].isna() for df in aligned_profiles.values()]
        common_mask = masks[0]
        for m in masks[1:]:
            common_mask &= m
        valid_index = np.where(common_mask.to_numpy())[0]

        for name, df in aligned_profiles.items():
            # cut profiles to valid range
            df_cut = df.iloc[valid_index].reset_index(drop=True)
            # take distance values from reference profiles
            df_cut["distance"] = reference_distance.iloc[:len(df_cut)].reset_index(drop=True)

            aligned_profiles[name] = df_cut

            if plot:
                title = f"Aligned: {name} to {reference_name} (Day {day})"
                plot_pairs([(aligned_profiles[reference_name], reference_name, df_cut, name)],
                            filename=f"day{day}_aligned_{name}_to_{reference_name}",
                            title=title,
                            save=True,
                            target_dir=target_dir)

        for name, df in aligned_profiles.items():
            smp_profiles[name] = df  # update original

        #save correlation results as csv
        if save:
            save_dir = Path("data/aligned_first")
            save_dir.mkdir(parents=True, exist_ok=True)

        for name, df in smp_profiles.items():
            df.to_csv(save_dir / f"{name}_aligned.csv", index=False)

    smp_profiles_shifted = smp_profiles.copy()
    return smp_profiles_shifted


if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()
    #to aligning two profiles
    smp_profiles_shifted = align_profiles(smp_profiles, pairs=True, plot=True, save=True)
    #to align all profiles to the first one of the day
    smp_profiles_shifted = align_profiles(smp_profiles, pairs=False, save=True)