# Automated processing + similarity scoring restricted to profiles with qa_flag == 1
# (the same profiles used for surface detection evaluation/tuning, see surfacedetection_evaluate).
# Produces one combined CSV with the similarity score of every profile pair in every
# raw_data day-folder, before and after cross-correlation alignment.
import csv
import configparser

from pathlib import Path
from itertools import combinations
from snowmicropyn import Profile

from code_SMP.detect_surface import detect_surface
from code_automated_correlation.a_automated_processing import get_offset, align_profiles
from code_automated_correlation.b_automated_similarity import similarity


def is_qa_flag_one(pnt_file):
    ini_file = pnt_file.with_suffix(".ini")
    config = configparser.ConfigParser()
    config.read(ini_file)
    try:
        qa_flag = int(config["quality assurance"].get("qa_flag", 0))
    except (KeyError, ValueError):
        qa_flag = 0
    return qa_flag == 1


def load_profiles_qa1(folder_path):
    profiles_dict = {}
    for pnt_file in folder_path.glob("*.PNT"):
        if not is_qa_flag_one(pnt_file):
            continue

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


def similarity_before_alignment(df1, df2):
    f1 = df1["force"].values
    f2 = df2["force"].values
    minlen = min(len(f1), len(f2))
    return similarity(f1[:minlen], f2[:minlen])


def process_folder(folder_path, csv_writer):
    day = folder_path.name
    smp_profiles = load_profiles_qa1(folder_path)

    profile_names = sorted(smp_profiles.keys())
    if len(profile_names) < 2:
        return 0

    n_pairs = 0
    for name1, name2 in combinations(profile_names, 2):
        df1 = smp_profiles[name1]
        df2 = smp_profiles[name2]

        score_before = similarity_before_alignment(df1, df2)

        offset_mm, _, lag = get_offset(df1, df2, name1, name2, plot=False)
        df1_aligned, df2_aligned = align_profiles(df1, df2, name1, name2, lag, plot=False)
        score_after = similarity(df1_aligned["force"].values, df2_aligned["force"].values)

        csv_writer.writerow([day, name1, name2, score_before, score_after, lag, offset_mm])
        n_pairs += 1

    return n_pairs


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    input_root = repo_root / "code_automated_correlation" / "raw_data"
    output_file = script_dir / "output" / "similarity_scores_qa1.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", newline="") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(["folder", "profile_name_1", "profile_name_2", "similarity_before", "similarity_after", "lag", "offset_mm"])

        for folder_path in sorted(input_root.iterdir()):
            if not folder_path.is_dir():
                continue
            print(f"Processing {folder_path.name}")
            n_pairs = process_folder(folder_path, csv_writer)
            f.flush()
            print(f"  -> {n_pairs} pairs written")

    print(f"Similarity scores saved to: {output_file}")
