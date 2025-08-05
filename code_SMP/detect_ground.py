import numpy as np

#from readSMP import load_all_smp_profiles

# method to cut the ground on the right moment -in pnt use original snowicropyn detect_ground

# detection method of snowmicropyn -changed to work for dfs to cut csv files
# https://github.com/slf-dot-ch/snowmicropyn/blob/master/snowmicropyn/detection.py
# overload = 42N 

def detect_ground_csv(df):
    """Automatic detection of ground (end of snowpack).

    :param snowmicropyn.Profile profile: The profile to detect ground in.
    :return: Distance where ground was detected.
    :rtype: float
    """

    force = df["force"]
    distance = df["distance"]

    ground = distance.iloc[-1]

    if force.max() >= 42: # overload property for all profiles
        i_ol = force.argmax()
        i_threshhold = np.where(distance.values >= distance.values[i_ol] - 20)[0][0]
        f_mean = np.mean(force.iloc[0:i_threshhold])
        f_std = np.std(force.iloc[0:i_threshhold])
        threshhold = f_mean + 5 * f_std # 5 sigma rule

        while force.iloc[i_ol] > threshhold:
            i_ol -= 10

        ground = distance.iloc[i_ol]

    #print(f"Detected ground at {ground} mm")
    return ground


#this kind of comment to avoid circular import 
"""""
if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()
    for name, profile in smp_profiles.items():
        ground_auto = detect_ground_csv(profile)
        force = profile["force"]
        distance = profile["distance"]
        #trim profile
        trimmed_df = profile[profile["distance"] <= ground_auto]

        # Plot results
        plt.figure(figsize=(8, 5))
        plt.plot(trimmed_df["distance"], trimmed_df["force"], label='Force (trimmed)')
        plt.axvline(x=ground_auto, color='red', linestyle='--', label='Auto Ground')
        plt.xlabel('Distance (mm)')
        plt.ylabel('Force (N)')
        plt.title(f'Ground Detection for {name}')
        plt.legend()
        plt.grid()
        plt.show()
"""""