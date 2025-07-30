import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from snowmicropyn import Profile
from scipy.signal import correlate

from code_visualizations.plotSMP import plot_pairs # function to plot to smp profiles together, not necessary for offset
from code_SMP.detect_surface import detect_surface  # my own method to detect surface
plt.style.use(r'c:/Users/jille/Documents/Uni/Master-Mechatronik/Masterarbeit/SMP-SignalProcessing/latex_default.mplstyle')


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

    #Print results
    #print(f"Crosscorrelation {name1} - {name2}")
    #print(f"Max corr: {np.max(correlation)}")
    #print(f"Offset: {offset_mm:.2f} mm (lag: {lag_max})")
    if plot == True:
        plt.figure(figsize=(5.5, 3.5)) #(8, 4))
        plt.plot(index_shifts_mm, correlation, label=f"Cross-Correlation: {name1}, {name2}")
        plt.axvspan(index_shifts_mm[start], index_shifts_mm[end], color='gray', alpha=0.2)
        #plt.title(f"Cross-Correlation over distance {name1} & {name2}")
        plt.xlabel("Distance (mm)")
        plt.ylabel("Correlation")
        plt.grid(True)
        #plt.show()
        plt.tight_layout()
        plt.legend(fontsize="small")
        plt.savefig(f"output/masterthesis/crosscorrelation{name1}_{name2}.svg") #this onyl for master thesis plots
        #plt.savefig(target_dir / f"corr_{name1}_{name2}.png")
        plt.close()

    return offset_mm, correlation, lag_max

def align_profiles(df1, df2, name1, name2, lag, plot=True, target_dir=Path("output/crosscorrelation")):
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
    df2_shifted["distance"] = df1_shifted["distance"]#

    if plot == True:
        title = f"Signal shifted with cross-Correlation {name1} & {name2}"
        filename = f"aligned_{name1}_to_{name2}"
        plot_pairs([(df1_shifted, name1, df2_shifted, name2)], filename, save=True, title=title, target_dir=target_dir)

    return df1_shifted, df2_shifted

if __name__ == "__main__":
    # Load all profiles from all days (means all folders)
    # Use default folder "./raw_data" in current directory
    root = Path(__file__).resolve().parent 
    input_root = root/ "raw_data"
    output_root = root / "output" / "crosscorrelation"

    all_day_profiles = {}

    for folder_path in sorted(input_root.iterdir()):
        if folder_path.is_dir():
            day = folder_path.name
            print(f"Processing {day}")
            smp_profiles = load_profiles(folder_path)
            all_day_profiles.update(smp_profiles)

    # Do crosscorellation for two profiles as a test
    df1 = all_day_profiles["S45M1056"]
    df2 = all_day_profiles["S45M1057"]
    # get offset
    offset_mm, correlation, lag = get_offset(df1, df2, "S45M1056", "S45M1057", plot=True, target_dir=output_root)
    # align profiles
    align_profiles(df1, df2, "S45M1056", "S45M1057", lag, plot=True, target_dir=output_root)