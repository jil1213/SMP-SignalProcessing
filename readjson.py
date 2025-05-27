import json
import pandas as pd
import matplotlib.pyplot as plt

import profiles_parameters #also correct? 
from profiles_parameters import LABELS, LABELS_LONG, COLORS #right? 

# load .json snowprofiles from LAWIS
def load_lawis_profile(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

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
    return df


def convert_to_snowdepth(df):
    # Converts the height written in the manual snow profile to snowdepth, same as used in SMP profiles 
    # Adds 'distance_min' and 'distance_max' coloumns
    max_height = df["height_max"].max()

    expanded_rows = []
    for _, row in df.iterrows():
            height_min = float(row["height_min"])
            height_max = float(row["height_max"])

            # First: Calculate lower boundary (height_min)
            expanded_rows.append({
                "distance": max_height - height_min,
                "hardness": row["hardness"],
                "hardness_id": row["hardness_id"],
                "grain1": row["grain1"],
                "grain2": row["grain2"]
            })

            # Then: calculate upper boundary (height_max)
            expanded_rows.append({
                "distance": max_height - height_max,
                "hardness": row["hardness"],
                "hardness_id": row["hardness_id"],
                "grain1": row["grain1"],
                "grain2": row["grain2"]
            })

    df_converted = pd.DataFrame(expanded_rows).reset_index(drop=True)
    return df_converted


def plot_lawis_hardness(df, name="LAWIS_Profile"):
    # plot step plot of hardness over distance
    plt.figure(figsize=(8, 5))
    #plt.step(df["distance"], df["hardness_id"], label=name)
    plt.plot(df["distance"], df["hardness_id"], label=name)

    plt.gca()
    plt.ylabel("Hardness (Index)")
    plt.xlabel("Distance from surface (mm)")
    plt.title(f"Hardness Profile: {name}")
    plt.grid()
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_lawis_colored_grain(df, name="LAWIS_Profile"):
    reverse_labels_long = {v.lower(): k for k, v in LABELS_LONG.items()}

    fig, ax = plt.subplots(figsize=(10, 2))

    for i in range(0, len(df), 2):
        left = df.iloc[i + 1]["distance"]
        right = df.iloc[i]["distance"]
        grain1_text = df.iloc[i]["grain1"].lower().strip()

        # Übersetze grain1 zu label_id über den LANGTEXT
        label_id = reverse_labels_long.get(grain1_text, 0)  # default zu 0 ("not_labelled")
        color = COLORS.get(label_id, "dimgray")

        ax.fill_betweenx([0, 1], left, right, color=color)

    ax.set_ylim(0, 1)
    ax.set_xlim(df["distance"].min(), df["distance"].max())
    ax.set_xlabel("Distance from surface (mm)")
    ax.set_yticks([])
    ax.set_title(name)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    #load profile day 1
    df_day1 = load_lawis_profile("data/LawisProfile23044.json")
    df_day1 = convert_to_snowdepth(df_day1)
    print(df_day1)
    #plot_lawis_hardness(df_day1, name="LAWIS Profile Day 1")

    #load profile day 2
    df_day2 = load_lawis_profile("data/LawisProfile23778.json")
    df_day2 = convert_to_snowdepth(df_day2)
    print(df_day2)
    #plot_lawis_hardness(df_day2, name="LAWIS Profile Day 2")
    plot_lawis_colored_grain(df_day1, name="LAWIS Profile Day 1")
    plot_lawis_colored_grain(df_day2, name="LAWIS Profile Day 2")