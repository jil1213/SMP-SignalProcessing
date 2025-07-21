import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
from code_SMP.readSMP import load_all_smp_profiles
from code_visualizations.plotSMP import bulid_pairs, plot_pairs
from code_automated_correlation.automated_processing import get_offset, align_profiles

target_dir = Path("output/cross_correlations")


def align_profiles_to_reference(smp_profiles, plot=True, save=False): 

    #case more than two profiles to compare
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
           df.to_csv(save_dir / f"{name}_alignedto{reference_name}.csv", index=False)

    smp_profiles_shifted = smp_profiles.copy()
    return smp_profiles_shifted


def align_pairs(smp_profiles, save_dir=None, plot=True, save=False): 
    #case only pairs to align and then save as csv
    #names of pairs are input statement
    paired_profiles = bulid_pairs(smp_profiles)
    for df1, name1, df2, name2 in paired_profiles:
        offset_mm, correlation, lag = get_offset(df1, df2, name1, name2)

        df1_shifted, df2_shifted = align_profiles(df1, df2, name1, name2, lag, plot=True)

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


    smp_profiles_shifted = smp_profiles.copy()
    return smp_profiles_shifted


if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()
    #to align two profiles
    smp_profiles_shifted = align_pairs(smp_profiles, plot=True, save=True)
    #to align all profiles to the first one of the day
    smp_profiles_shifted = align_profiles_to_reference(smp_profiles, save=True)