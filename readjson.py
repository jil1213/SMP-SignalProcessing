import json
import pandas as pd
from pathlib import Path

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
    #Converts the height written in the manual snow profile to snowdepth, same as used in SMP profiles 
    #Adds 'distance_min' and 'distance_max' coloumns
    max_height = df["height_max"].max()
    df["distance_min"] = max_height - df["height_max"]
    df["distance_max"] = max_height - df["height_min"]
    return df


if __name__ == "__main__":
    # Beispiel-Anwendung
    #load profile day 1
    df_day2 = load_lawis_profile("data/LawisProfile23044.json")
    #load profile day 2
    df_day2 = load_lawis_profile("data/LawisProfile23778.json")
    df_day2 = convert_to_snowdepth(df_day2)
    print(df_day2)