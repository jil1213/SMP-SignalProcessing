import numpy as np
import matplotlib.pyplot as plt


from pathlib import Path
from itertools import combinations
from snowmicropyn import Profile
from scipy.signal import correlate

from code_automated_correlation.new_surface_detection import detect_surface # my own method to detect surface


def load_profiles(folder_path):
    profiles_dict = {}
    for pnt_file in folder_path.glob("*.PNT"):
        smp_profile = Profile.load(pnt_file)
        name = smp_profile.name
        df = smp_profile.samples

        # Trim surface and ground
        ground = Profile.detect_ground(smp_profile)
        surface, _, _ = detect_surface(df[df["distance"] <= ground], name)
        df = df[(df["distance"] >= surface) & (df["distance"] <= ground)].copy()
        df["distance"] -= surface  # Reset distance so it starts at 0

        profiles_dict[name] = df

    return profiles_dict


def plot_pairs(pairs, label2, filename, target_dir=Path("output/visualizations")):
    for df1, name1, df2, name2 in pairs:
        plt.figure(figsize=(5.5, 3.5))
        plt.plot(df1["distance"], df1["force"], label=name1)
        plt.plot(df2["distance"], df2["force"], label=label2)
        plt.xlabel("Distance (mm)")
        plt.ylabel("Force (N)")
        plt.legend()
        plt.grid()
        plt.tight_layout()
        plt.savefig((target_dir / filename).with_suffix(".svg"))
        plt.close()


#method to get the offset of two profiles by crosscorrelation
def get_offset(df1, df2, name1, name2, plot=True, target_dir=Path("output/crosscorrelation")):

    # make sure index starts with 0 -> surface detection earlier might make trouble here
    df1 = df1.reset_index(drop=True)
    df2 = df2.reset_index(drop=True)

    # Cut dfs to apply autocorrelation - only use for offset method!
    start = 0
    end = min(len(df1), len(df2))- 24200 # cut off last 24.200 values (=100mm), because they sometimes include ground peaks

    # check if array is long enough to cut of 100mm, if not: take smaller range
    if end < 0:
        print(f"Profile is too short, using smaller range for cross-correlation.")
        start = 0
        end = min(len(df1), len(df2))

    df1_cut = df1.iloc[start:end].reset_index(drop=True)
    df2_cut = df2.iloc[start:end].reset_index(drop=True)

    # Calculate cross-correlation to cutted dfs with scipy FFT correlate (faster than np.correlate))
    correlation = correlate(df1_cut["force"], df2_cut["force"], mode='full', method='fft')

    dx = np.mean(np.diff(df1_cut["distance"]))  # mean spacing in mm

    index_shifts = np.arange(-len(df1_cut["force"]) + 1, len(df1_cut["force"])) # create array of right size, starting from -n+1 to n
    index_shifts_mm = index_shifts * dx #convert lags into distances in mm

    # Lag with max correlation 
    # lag_max = np.argmax(correlation) - (len(df1_cut["force"]) - 1) # lag with max correlation global
    # local max  around center (most realistic)
    start, end = len(correlation) // 2 - 24200, len(correlation) // 2 + 24200 # Assumption: max shift is not more than 100cm in both directions
    lag_local = np.argmax(correlation[start:end])
    lag_max = (start + lag_local) - (len(df1_cut["force"]) - 1) #  absolute index of whole array - centre

    offset_mm = lag_max * dx #distance offset

    if plot == True:
        plt.figure(figsize=(5.5, 3.5)) #(8, 4))
        plt.plot(index_shifts_mm, correlation, label=f"Cross-Correlation: {name1}, {name2}")
        plt.axvspan(index_shifts_mm[start], index_shifts_mm[end], color='gray', alpha=0.2)
        plt.xlabel("Distance (mm)")
        plt.ylabel("Correlation")
        plt.grid()
        plt.tight_layout()
        plt.legend(fontsize="small")
        filename = f"crosscorrelation_{name1}_{name2}.svg"
        plt.savefig(target_dir / filename)
        plt.close()

    return offset_mm, correlation, lag_max

def align_profiles(df1, df2, name1, name2, lag, plot=True, target_dir=Path("output/crosscorrelation")):
    # plot profiles before alignment
    if plot == True:
        # calculate similarity score before alignment 
        #take only min len of both to calculate
        f1 = df1["force"].values
        f2 = df2["force"].values
        minlen = min(len(df1), len(df2))
        b_cosine = np.dot(f1[:minlen], f2[:minlen]) / (np.linalg.norm(f1[:minlen]) * np.linalg.norm(f2[:minlen]))
        # convert cosine value to string without . 
        cos_str = f"{b_cosine:.4f}".replace("0.", "0p")
        label2=name2
        filename = f"{name1}_to_{name2}_before_alignment_{cos_str}"
        plot_pairs([(df1, name1, df2, name2)], label2, filename, target_dir=target_dir)

    df2_shifted = df2.copy()
    # shift indices of df2 with lag to get max correlation
    # positive lag shift to right side - negative lag shift to left side
    df2_shifted['force'] = df2_shifted['force'].shift(lag, fill_value=np.nan)

    # bring both to same length
    min_len = min(len(df1), len(df2_shifted))
    df1 = df1.iloc[:min_len].reset_index(drop=True) #reset index back to zero (surrface did set higher than 0 before)
    df2_shifted = df2_shifted.iloc[:min_len].reset_index(drop=True)

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

    offset_mm = lag * np.mean(np.diff(df1["distance"]))
    # plot profiles after alignment
    if plot == True:
        label2 = f"shifted {name2}"
        filename = f"{name1}_to_{name2}_with_alignment_lag{lag}"
        plot_pairs([(df1_shifted, name1, df2_shifted, name2)], label2, filename, target_dir=target_dir)

    return df1_shifted, df2_shifted

if __name__ == "__main__":
    # Load all profiles from all days (means all folders)
    # Use default folder "./raw_data" in current directory
    root = Path(__file__).resolve().parent 
    input_root = root/ "raw_data"
    output_root = root / "output" / "crosscorrelation"

    for folder_path in sorted(input_root.iterdir()):
        if folder_path.is_dir():
            day = folder_path.name
            print(f"Processing {day}")
            smp_profiles = load_profiles(folder_path)

            # Output directory for this day
            day_output_dir = root / "output" / "alignment" / day
            day_output_dir.mkdir(parents=True, exist_ok=True)

            profile_names = sorted(smp_profiles.keys())
            for name1, name2 in combinations(sorted(profile_names), 2):
                df1 = smp_profiles[name1]
                df2 = smp_profiles[name2]

                # calculate offset and align
                offset_mm, correlation, lag = get_offset(df1, df2, name1, name2, plot=True, target_dir=day_output_dir)
                align_profiles(df1, df2, name1, name2, lag, plot=True, target_dir=day_output_dir)
                
            # Only for master thesis visualization!
            for name in profile_names:
                if name == 'S45M1064':
                    df = smp_profiles[name]
                    plt.figure(figsize=(5.5, 3.5)) #(8, 4))
                    plt.plot(df["distance"], df["force"], label=name)
                    plt.xlabel("Distance (mm)")
                    plt.ylabel("Force (N)")
                    plt.grid()
                    plt.tight_layout()
                    plt.legend()
                    filename = f"single_profile_{name}.svg"
                    plt.savefig(day_output_dir / filename)
                    plt.close()

                    # zoomed range 
                    plt.figure(figsize=(5.5, 3.5)) #(8, 4))
                    plt.plot(df["distance"], df["force"])
                    plt.xlabel("Distance (mm)")
                    plt.ylabel("Force (N)")
                    plt.xlim(199.8, 200.6)
                    plt.ylim(0.1, 0.25)
                    plt.grid()
                    plt.tight_layout()
                    filename = f"single_profile_{name}_zoomed.svg"
                    plt.savefig(day_output_dir / filename)
                    plt.close()