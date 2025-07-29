from code_automated_correlation.automated_processing import load_profiles, get_offset, align_profiles
from code_SMP.detect_surface import detect_surface
import matplotlib.pyplot as plt
plt.style.use(r'c:/Users/jille/Documents/Uni/Master-Mechatronik/Masterarbeit/SMP-SignalProcessing/latex_default.mplstyle')
from pathlib import Path

if __name__ == "__main__":
    # Load profiles
    folder_path = Path("data/smp_profiles")
    profiles_dict = load_profiles(folder_path)

    # Graphics for Results Part 2.1 Alignment 

    # Dictionary of profile names for each day
profiles_by_day = {
    1: ("S45M1058", "S45M1064"),
    2: ("S45M1084", "S45M1090"),
}

for day, (name1, name2) in profiles_by_day.items():
    df1 = profiles_dict[name1]
    df2 = profiles_dict[name2]

    # Plot profiles without alignment
    plt.figure(figsize=(5.5, 3.5))
    plt.plot(df1["distance"], df1["force"], label=name1)
    plt.plot(df2["distance"], df2["force"], label=name2)
    plt.xlabel("Distance (mm)")
    plt.ylabel("Force (N)")
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.savefig(f"output/masterthesis/profiles_day{day}_without_alignment.svg")
    plt.close()

    # Calculate offset and align profiles
    offset_mm, correlation, lag = get_offset(df1, df2, name1, name2, plot=False)
    df1_aligned, df2_aligned = align_profiles(df1, df2, name1, name2, lag, plot=False)

    # Plot aligned profiles
    plt.figure(figsize=(5.5, 3.5))
    plt.plot(df1_aligned["distance"], df1_aligned["force"], label=name1)
    plt.plot(df2_aligned["distance"], df2_aligned["force"], label=f"shifted {name2}")
    plt.xlabel("Distance (mm)")
    plt.ylabel("Force (N)")
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.savefig(f"output/masterthesis/profiles_day{day}_with_alignment.svg")
    plt.close()