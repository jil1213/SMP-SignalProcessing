from pathlib import Path
from snowmicropyn import Profile

from code_SMP.detect_surface import detect_surface  # my own method to detect surface


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


if __name__ == "__main__":
    # Load all profiles from all days (means all folders)
    # Use default folder "./raw_data" in current directory
    input_root = Path(__file__).resolve().parent / "raw_data"

    all_day_profiles = {}

    for folder_path in sorted(input_root.iterdir()):
        if folder_path.is_dir():
            print(f"Processing {folder_path.name}")
            profiles = load_profiles(folder_path)
            all_day_profiles.update(profiles)