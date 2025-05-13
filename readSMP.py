import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

from pathlib import Path # for os independent path handling
from snowmicropyn import Profile, detection #.detect_ground, detection.detect_surface #package snowmicropyn must be installed
from detect_ground import detect_ground_csv #original method from snowmicropyn changed to work with csv files

#todo: handle/detecting ground and surface? (especially ground should be removed..)

# read SMP .pnt files and export them as csv files 
# inspired by snowdragon/data_handling/data_preprocessing.py
def export_pnt(pnt_dir, target_dir,  overwrite=False):
    """ Exports all pnt files from a dir and its subdirs as csv files into a new dir.
    Preproceses the profiles, according to kwargs arguments.
    Parameters:
        pnt_dir (Path): folder location of pnt files (in our case the smp profiles)
        target_dir (Path): folder name where converted csv files should get exported or were they have already been exported
        overwrite (Boolean): indicates if csv file should be overwriting if csv file already exists
    """
    # create dir for csv exports
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)

    # match all files in the dir who end on .pnt recursively
    match_pnt = pnt_dir.as_posix() + "/**/*.pnt"
    # use generator to reduce memory usage
    file_generator = glob.iglob(match_pnt, recursive=True)
    # yields each matching file and exports it
    for file in file_generator:
        file_name = Path(target_dir, file.split("/")[-1].split(".")[0] + "." + "csv")
        # exports file only if we want to overwrite it or it doesnt exist yet
        if overwrite or not file_name.is_file():
            smp_profile = Profile.load(file)
            df = smp_profile.samples
            df.to_csv(os.path.join(target_dir, Path(smp_profile.name + ".csv")))

    print("Finished exporting all pnt file as {} files in {}.".format("csv", target_dir))


#target_dir = Path("data/smp_profiles_csv")
#pnt_dir = Path("data/smp_profiles")
#export_pnt(pnt_dir, target_dir, overwrite=True)


#trim profiles with surface and ground 
#autodetection by snowmicropyn package and option to change values manually
#Markers can be taken out of Allocation File or set with autodetect and manually corrected
def trim_profile(profile, Allocation = True):
    df = profile.samples
    allocation = pd.read_excel("data/smp_allocation.xlsx")

    if Allocation == True: 
        profile_data = allocation[allocation["name"] == profile.name].iloc[0]
        ground = profile_data["Ground"]
        surface = profile_data["Surface"]
        print(f"Using allocated markers: Surface = {surface} mm, Ground = {ground} mm")
        df_trimmed = df[(df["distance"] >= surface) & (df["distance"] <= ground)]
        return df_trimmed

    else: 
        ground = Profile.detect_ground(profile)
        surface = Profile.detect_surface(profile)

        while True:
            # Plot to check if algorithm is right
            plt.figure(figsize=(8, 5))
            plt.plot(df["distance"], df["force"])
            plt.axvline(x=ground, color='red', linestyle='--', label=f'Ground: {ground} mm')
            plt.axvline(x=surface, color='blue', linestyle='--', label=f'Surface: {surface} mm')
            plt.xlabel("Distance (mm)")
            plt.ylabel("Force (N)")
            plt.grid()
            plt.legend()
            plt.show()

            # Option to manually change the values for surface and ground 
            response = input("Are Markers correct? (y/n): ").strip().lower()

            if response == 'y':
                print("Proceeding with trimming...")
                df_trimmed = df[(df["distance"] >= surface) & (df["distance"] <= ground)]
                return df_trimmed
            elif response == 'n':
                print("Please enter custom values for surface and ground.")
                try:
                    # Terminal user input
                    surface = float(input("Enter value for Surface (in mm): ").strip())
                    ground = float(input("Enter value for Ground (in mm): ").strip())
                    print(f"Custom values set: Surface = {surface} mm, Ground = {ground} mm")
                except ValueError:
                    print("Invalid input. Please enter numeric values for surface and ground.")
            else:
                print("Invalid input. Please enter 'y' for Yes or 'n' for No.")

#load files as data frame
def load_pnt(file, Trim_ground = True, Trim = False):
    smp_profile = Profile.load(file)
    profile_name = smp_profile.name #string
    spatial_resolution = smp_profile.spatial_resolution #float
    if Trim == True: 
        df_trimmed = trim_profile(smp_profile) #loaded smp Profile must be given as input parameter
        df = df_trimmed
    elif Trim_ground == True:
        ground = Profile.detect_ground(smp_profile)
        df = smp_profile.samples
        df = df[df["distance"] <= ground]
    else: 
        df = smp_profile.samples # converting profile into a panda dataframe
    return df, profile_name, spatial_resolution

def load_csv(file, Trim_ground = True):
    profile_name = Path(file).stem
    df = pd.read_csv(file)
    if Trim_ground == True:
        ground = detect_ground_csv(df)
        df = df[df["distance"] <= ground]
    return df, profile_name

def plot_profiles(profiles, filename, save=True, target_dir=Path("output/visualizations")):
    plt.figure(figsize=(8, 5))
    for df, name in profiles:
        plt.plot(df["distance"], df["force"], label=name)  # more than one profile can be plotted
    plt.xlabel("Distance (mm)")
    plt.ylabel("Force (N)")
    plt.title(f"{filename}")
    plt.legend()
    plt.grid()
    if save == True: 
        # save as figure png
        plt.savefig((target_dir / filename).with_suffix(".png"))
        #save as pdf for better quality in another folder
        (target_dir / "pdf").mkdir(parents=True, exist_ok=True)
        plt.savefig((target_dir / "pdf" / filename).with_suffix(".pdf"), format="pdf", bbox_inches="tight")
    else:
        plt.show()
    plt.close()


smp_profiles = {} #dictionary for all smp profiles

def load_all_smp_profiles(pnt=True):
    allocation = pd.read_excel("data/smp_allocation.xlsx")
    for i in range(allocation.shape[0]): 
        spatial_res = 0.00413223123177886 # default but gets checked again in pnts 
        if pnt == True:
            df, profile_name, spatial_res = load_pnt("data/smp_profiles/"+allocation["name"][i]+ ".PNT")
        else:
            df, profile_name = load_csv("data/aligned_first/"+allocation["name"][i]+ "_aligned.csv")
        df.attrs["date"] = allocation["date"][i]
        df.attrs["velocity"] = allocation["velocity"][i]
        df.attrs["spatial_resolution"] = spatial_res
        smp_profiles[profile_name] = df 
    return smp_profiles

#example:plot two SMP profiles
#plot_profiles([(smp_profiles["S45M1053"], "SMP_1"), (smp_profiles["S45M1056"], "SMP_2")])