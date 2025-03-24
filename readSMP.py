import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

from pathlib import Path # for os independent path handling
from snowmicropyn import Profile #package snowmicropyn must be installed

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


#load files as data frame
def load_pnt(file):
    smp_profile = Profile.load(file)
    profile_name = smp_profile.name #string
    df = smp_profile.samples # converting profile into a panda dataframe
    return df, profile_name

def plot_profiles(profiles, filename, save=False, target_dir=Path("output/visualizations")):
    plt.figure(figsize=(8, 5))
    for df, name in profiles:
        plt.plot(df["distance"], df["force"], label=name)  # more than one profile can be plotted
    plt.xlabel("Distance (cm)")
    plt.ylabel("Force (N)")
    plt.title(f"{filename}")
    plt.legend()
    plt.grid()
    #plt.show()
    if save == True: 
        # save as figure
        plt.savefig((target_dir / filename).with_suffix(".png"))
        plt.close()


smp_profiles = {} #dictionary for all smp profiles

def load_all_smp_profiles():
    allocation = pd.read_excel("data/smp_allocation.xlsx")
    for i in range(allocation.shape[0]): 
        df, profile_name = load_pnt("data/smp_profiles/"+allocation["name"][i]+ ".PNT")
        df.attrs["date"] = allocation["date"][i]
        df.attrs["velocity"] = allocation["velocity"][i]
        smp_profiles[profile_name] = df 
    return smp_profiles

#example:plot two SMP profiles
#plot_profiles([(smp_profiles["S45M1053"], "SMP_1"), (smp_profiles["S45M1056"], "SMP_2")])