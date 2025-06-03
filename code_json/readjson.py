import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from code_json.profiles_parameters import LABELS_LONG, COLORS


def resample_lawis_profile(df, name):
    # Resample LAWIS profiles to SMP resolution and extract layer boundaries

    # fix resolution of SMP
    resolution = 0.00413223123177886 #mm

    # Step 1: Extract min/max distance
    min_dist = df["distance"].min()
    max_dist = df["distance"].max()

    # Step 2: Create uniform distance values
    distances = np.arange(min_dist, max_dist, resolution)

    # Step 3: Create intervalls for all layers
    intervals = []
    rows = []
    for i in range(0, len(df) - 1, 2):
        top = df.iloc[i]["distance"]
        bottom = df.iloc[i + 1]["distance"]
        intervals.append(pd.Interval(left=bottom, right=top, closed='left'))  # [bottom, top)
        rows.append(df.iloc[i])

    # Step 4: Mapping with IntervalIndex
    interval_index = pd.IntervalIndex(intervals)
    mapping_df = pd.DataFrame(rows).reset_index(drop=True)

    # Step 5: Allocate all points
    distance_series = pd.Series(distances, name="distance")
    bin_indices = interval_index.get_indexer(distance_series)  # -1 if not found in any interval

    # Step 6: Build resampled DataFrame
    resampled_df = mapping_df.iloc[bin_indices].reset_index(drop=True)
    resampled_df["distance"] = distances
    resampled_df.loc[bin_indices == -1, resampled_df.columns != "distance"] = np.nan  # empty layer (not sure if necessary)

    boundaries = pd.DataFrame({"distance": df["distance"].sort_values().unique()})

    # save both as csv, but not necessary right now
    #resampled_df.to_csv(Path(f"data/resampled_{name}.csv") , index=False)
    #boundaries.to_csv(Path(f"data/boundaries_{name}.csv"), index=False)

    return resampled_df, boundaries

# load .json snowprofiles from LAWIS
def load_lawis_profile(json_path, resample=True):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    json_path = Path(json_path)

    layers = data["profile"]

    records = []
    for layer in layers:
        record = {
            "height_min": layer["height"]["min"],
            "height_max": layer["height"]["max"],
            "hardness": layer["hardness"]["text"],
            "hardness_id": layer["hardness"]["id"],
            "grain1": layer["grain"]["shape1"]["text"],
            "grain2": layer["grain"]["shape2"]["text"],
            "grain_size_min": layer["grain"]["size"]["min"],
            "grain_size_max": layer["grain"]["size"]["max"]
        }
        records.append(record)

    df = pd.DataFrame(records)

    # Converts the height written in the manual snow profile to snowdepth, same as used in SMP profiles
    # Adds 'distance_min' and 'distance_max' coloumns
    max_height = df["height_max"].max()

    expanded_rows = []
    for _, row in df.iterrows():
            height_min = float(row["height_min"])
            height_max = float(row["height_max"])

            # First: Calculate lower boundary (height_min)
            expanded_rows.append({
                "distance": (max_height - height_min)*10, #convert cm to
                "hardness": row["hardness"],
                "hardness_id": row["hardness_id"],
                "grain1": row["grain1"],
                "grain2": row["grain2"]
            })

            # Then: calculate upper boundary (height_max)
            expanded_rows.append({
                "distance": (max_height - height_max)*10, #convert cm to mm
                "hardness": row["hardness"],
                "hardness_id": row["hardness_id"],
                "grain1": row["grain1"],
                "grain2": row["grain2"]
            })

    df = pd.DataFrame(expanded_rows).reset_index(drop=True)

    # Assign color of snow grain types to df
    # using defined Labels in profiles_parameters.py

    reverse_labels_long = {v.lower(): k for k, v in LABELS_LONG.items()}

    colors = []
    for grain in df["grain1"]:
        grain_text = str(grain).lower().strip()
        label_id = reverse_labels_long.get(grain_text, 0)
        color = COLORS.get(label_id, "dimgray")
        colors.append(color)
    df["color"] = colors

    if resample==True:
        df, boundaries = resample_lawis_profile(df, json_path.stem)  # Resample to SMP resolution
    else:
        boundaries = pd.DataFrame({"distance": df["distance"].sort_values().unique()})
    return df, boundaries

# plot hardness index over profile depth
def plot_lawis_hardness(df, name="LAWIS_Profile"):
    plt.figure(figsize=(8, 5))
    plt.plot(df["distance"], df["hardness_id"], label=name)

    plt.gca()
    plt.ylabel("Hardness (Index)")
    plt.xlabel("Distance from surface (mm)")
    plt.title(f"Hardness Profile: {name}")
    plt.grid()
    plt.legend()
    plt.tight_layout()
    plt.show()

#plot colors and hardness over profile depth
def plot_lawis_colored_grain(df, name="LAWIS_Profile"):
    fig, ax = plt.subplots(figsize=(10, 2))

    current_color = df["color"].iloc[0]
    start = df["distance"].iloc[0]

    for i in range(1, len(df)):
        color = df["color"].iloc[i]
        if color != current_color or i == len(df) - 1:
            end = df["distance"].iloc[i]
            ax.fill_betweenx([0, 1], start, end, color=current_color)
            start = end
            current_color = color

    # hardness
    ax2 = ax.twinx()
    ax2.plot(df["distance"], df["hardness_id"], color='black', linewidth=1.5, label="Hardness")
    ax2.set_ylim(df["hardness_id"].min() - 0.5, df["hardness_id"].max() + 0.5)
    ax2.set_ylabel("Hardness (Index)")
    ax2.legend()

    ax.set_xlim(df["distance"].min(), df["distance"].max())
    ax.set_xlabel("Distance from surface (mm)")
    ax.set_yticks([])
    ax.set_title(name)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    #load profile day 1
    df_day1, boundaries1 = load_lawis_profile("data/LawisProfile23044.json")

    plot_lawis_hardness(df_day1, name="LAWIS Profile Day 1")
    plot_lawis_colored_grain(df_day1, name="LAWIS Profile Day 1")


    #load profile day 2
    df_day2, boundaries2 = load_lawis_profile("data/LawisProfile23778.json")

    plot_lawis_hardness(df_day2, name="LAWIS Profile Day 2")
    plot_lawis_colored_grain(df_day2, name="LAWIS Profile Day 2")