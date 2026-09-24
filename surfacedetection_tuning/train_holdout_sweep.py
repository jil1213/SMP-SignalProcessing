# Trains force_threshold parameters (confirm_mode="force": k, and confirm_mode="persistence":
# min_persist_frac) on a 70% split of the raw_data profiles, so the remaining 30% held-out
# profiles can be evaluated independently in surfacedetection_evaluate/evaluate_holdout.py
# without ever being seen during parameter selection.
import numpy as np
import pandas as pd
import configparser
import pickle

from pathlib import Path
from snowmicropyn import Profile
from snowmicropyn.tools import smooth
from sklearn.metrics import mean_absolute_error, mean_squared_error
from code_SMP.detect_surface import detect_surface, moving_linear_regression

SPLIT_DIR = Path(__file__).resolve().parent / "train_test_split"
SPLIT_PATH = SPLIT_DIR / "profile_split.csv"
RAW_DATA_PATH = Path(__file__).resolve().parent.parent / "code_automated_correlation" / "raw_data"
TRAIN_FRAC = 0.7
SPLIT_SEED = 42


def build_profile_pool(folder_path):
    # same filtering logic as calculate_surfaces() in surfacedetection_evaluate/evaluate_surfacedetection.py
    records = []
    for file in folder_path.rglob("*.PNT"):
        folder_name = file.parent.name
        if folder_name.startswith("202501") or folder_name.endswith("T"):
            continue

        ini_file = file.with_suffix(".ini")
        config = configparser.ConfigParser()
        config.read(ini_file)

        try:
            qa_flag = int(config["quality assurance"].get("qa_flag", 0))
        except (KeyError, ValueError):
            qa_flag = 0
        if qa_flag != 1:
            continue

        try:
            surface_ini = float(config["markers"]["surface"])
        except (KeyError, ValueError):
            continue

        records.append(dict(
            profile_name=file.stem,
            file_path=str(file.relative_to(folder_path.parent.parent)),
            surface_ini=surface_ini,
        ))
    return records


def build_or_load_split(folder_path, split_path, train_frac=TRAIN_FRAC, seed=SPLIT_SEED):
    if split_path.exists():
        print(f"Reusing existing split: {split_path}")
        return pd.read_csv(split_path)

    records = build_profile_pool(folder_path)
    df = pd.DataFrame(records)

    rng = np.random.default_rng(seed)
    shuffled_idx = rng.permutation(len(df))
    n_train = int(round(train_frac * len(df)))
    split = np.full(len(df), "test", dtype=object)
    split[shuffled_idx[:n_train]] = "train"
    df["split"] = split

    split_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(split_path, index=False)
    print(f"Built new split ({(split == 'train').sum()} train / {(split == 'test').sum()} test) -> {split_path}")
    return df


def compute_precomputed(file_path):
    smp_profile = Profile.load(file_path)
    df = smp_profile.samples
    distance = df["distance"].reset_index(drop=True)
    force = df["force"].reset_index(drop=True)
    window_len = 242

    grad = moving_linear_regression(distance, force, window_mm=1.0)
    grad = smooth(grad, window_len)
    grad = grad[:len(distance)]

    max_distance_mm = 100.0
    window = int(20 / 0.00413223123177886)
    min_std = np.inf
    air_force_mean = None
    air_force_std = None
    grad_air = grad[distance <= (distance[0] + max_distance_mm)]
    force_air = force[distance <= (distance[0] + max_distance_mm)].reset_index(drop=True).to_numpy()
    for i in range(len(grad_air) - window + 1):
        window_grad = grad_air[i : i + window]
        s = window_grad.std()
        if s < min_std:
            min_std = s
            air_std = s
            air_force_mean = force_air[i : i + window].mean()
            air_force_std = force_air[i : i + window].std()
    threshold = 5 * air_std

    return distance, force, grad, threshold, air_force_mean, air_force_std


def outlier_counts(delta, thresholds=(50, 100)):
    return {f"n_above_{t}mm": int(np.sum(np.abs(delta) > t)) for t in thresholds}


def sweep(train_profiles, param_name, param_values, **fixed_kwargs):
    rows = []
    for value in param_values:
        kwargs = {**fixed_kwargs, param_name: value}
        surface_ini_all = []
        surface_new_all = []
        for name, precomputed, surface_ini in train_profiles:
            surface_new, grad, threshold = detect_surface(None, name, precomputed=precomputed, **kwargs)
            surface_ini_all.append(surface_ini)
            surface_new_all.append(surface_new)

        surface_ini_all = np.array(surface_ini_all)
        surface_new_all = np.array(surface_new_all)
        delta = surface_new_all - surface_ini_all

        row = dict(
            **{param_name: value},
            mae=mean_absolute_error(surface_ini_all, surface_new_all),
            rmse=np.sqrt(mean_squared_error(surface_ini_all, surface_new_all)),
            **outlier_counts(delta),
        )
        rows.append(row)
        print(f"{param_name}={value:.3f} -> MAE={row['mae']:.2f} mm, RMSE={row['rmse']:.2f} mm, "
              f"{row['n_above_50mm']} |delta|>50mm, {row['n_above_100mm']} |delta|>100mm")

    return pd.DataFrame(rows)


if __name__ == "__main__":
    split_df = build_or_load_split(RAW_DATA_PATH, SPLIT_PATH)
    train_rows = split_df[split_df["split"] == "train"]
    print(f"Training on {len(train_rows)} profiles ({len(split_df) - len(train_rows)} held out for evaluation).")

    root = Path(__file__).resolve().parent.parent
    precomputed_cache_path = SPLIT_DIR / "train_precomputed.pkl"
    if precomputed_cache_path.exists():
        print(f"Reusing cached precomputed train data: {precomputed_cache_path}")
        with precomputed_cache_path.open("rb") as f:
            train_profiles = pickle.load(f)
    else:
        train_profiles = []
        for _, row in train_rows.iterrows():
            precomputed = compute_precomputed(root / row["file_path"])
            train_profiles.append((row["profile_name"], precomputed, row["surface_ini"]))
        with precomputed_cache_path.open("wb") as f:
            pickle.dump(train_profiles, f)

    print("\n--- Sweeping k (confirm_mode='force') ---")
    k_values = np.arange(0.5, 6.0 + 1e-9, 0.25)
    results_force = sweep(train_profiles, "k", k_values, confirm_mode="force", use_air_mean=True)
    results_force.to_csv(SPLIT_DIR / "sweep_force.csv", index=False)
    best_force = results_force.sort_values("rmse").iloc[0]

    print("\n--- Sweeping min_persist_frac (confirm_mode='persistence') ---")
    frac_values = np.concatenate([np.arange(0.1, 0.95, 0.05), np.arange(0.95, 1.0 + 1e-9, 0.01)])
    results_persistence = sweep(train_profiles, "min_persist_frac", frac_values, confirm_mode="persistence")
    results_persistence.to_csv(SPLIT_DIR / "sweep_persistence.csv", index=False)
    best_persistence = results_persistence.sort_values("rmse").iloc[0]

    best_config = dict(
        force=dict(k=float(best_force["k"]), use_air_mean=True,
                   mae=float(best_force["mae"]), rmse=float(best_force["rmse"])),
        persistence=dict(min_persist_frac=float(best_persistence["min_persist_frac"]),
                          mae=float(best_persistence["mae"]), rmse=float(best_persistence["rmse"])),
    )
    import json
    with (SPLIT_DIR / "best_config.json").open("w", encoding="utf-8") as f:
        json.dump(best_config, f, indent=2)

    print(f"\nBest force config: k={best_force['k']:.2f} -> MAE={best_force['mae']:.2f} mm, RMSE={best_force['rmse']:.2f} mm")
    print(f"Best persistence config: min_persist_frac={best_persistence['min_persist_frac']:.2f} -> "
          f"MAE={best_persistence['mae']:.2f} mm, RMSE={best_persistence['rmse']:.2f} mm")
    print(f"\nSaved: {SPLIT_DIR / 'sweep_force.csv'}, {SPLIT_DIR / 'sweep_persistence.csv'}, "
          f"{SPLIT_DIR / 'best_config.json'}")
