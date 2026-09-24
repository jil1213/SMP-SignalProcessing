# Evaluates the best force-threshold k chosen by surfacedetection_tuning/train_holdout_sweep.py
# on the 30% of raw_data profiles that were held out of that training sweep.
import json
import pandas as pd

from pathlib import Path
from snowmicropyn import Profile
from sklearn.metrics import mean_absolute_error, mean_squared_error
from code_SMP.detect_surface import detect_surface
from surfacedetection_tuning.tune_surfacedetection import compute_metrics, plot_delta_error

root = Path(__file__).resolve().parent.parent
SPLIT_PATH = root / "surfacedetection_tuning" / "train_test_split" / "profile_split.csv"
BEST_CONFIG_PATH = root / "surfacedetection_tuning" / "train_test_split" / "best_config.json"
CACHE_PATH = Path(__file__).resolve().parent / "holdout" / "surface_detection_holdout_cache.csv"

use_cache = True


def calculate_holdout_surfaces(test_rows, best_config):
    results = []
    for _, row in test_rows.iterrows():
        smp_profile = Profile.load(root / row["file_path"])
        name = smp_profile.name
        df = smp_profile.samples

        surface_old = Profile.detect_surface(smp_profile)
        surface_force, _, _ = detect_surface(
            df, name, k=best_config["force"]["k"], use_air_mean=best_config["force"]["use_air_mean"],
            confirm_mode="force",
        )

        results.append(dict(
            profile_name=name,
            surface_ini=row["surface_ini"],
            surface_old=surface_old,
            surface_force=surface_force,
        ))
    return results


if __name__ == "__main__":
    split_df = pd.read_csv(SPLIT_PATH)
    test_rows = split_df[split_df["split"] == "test"]
    print(f"Evaluating on {len(test_rows)} held-out profiles.")

    with BEST_CONFIG_PATH.open("r", encoding="utf-8") as f:
        best_config = json.load(f)

    if use_cache and CACHE_PATH.exists():
        print(f"Using existing holdout cache: {CACHE_PATH}")
        df_results = pd.read_csv(CACHE_PATH)
    else:
        results = calculate_holdout_surfaces(test_rows, best_config)
        df_results = pd.DataFrame(results)
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        df_results.to_csv(CACHE_PATH, index=False)
        print(f"Holdout surface results saved to: {CACHE_PATH}")

    surface_ini_all = df_results["surface_ini"].values
    surface_old_all = df_results["surface_old"].values
    surface_force_all = df_results["surface_force"].values

    # Quick side-by-side comparison against the manual reference
    print("\nHeld-out comparison (existing vs. force-threshold):")
    for label, surface_all in (
        ("Existing (snowmicropyn)", surface_old_all),
        (f"Force (k={best_config['force']['k']:.2f})", surface_force_all),
    ):
        mae = mean_absolute_error(surface_ini_all, surface_all)
        rmse = mean_squared_error(surface_ini_all, surface_all) ** 0.5
        print(f"  {label}: MAE={mae:.2f} mm, RMSE={rmse:.2f} mm")

    # Detailed metrics + boxplots, reusing the existing plotting code
    output_force = Path(__file__).resolve().parent / "holdout" / "force"
    output_force.mkdir(parents=True, exist_ok=True)

    scores_force = compute_metrics(surface_ini_all, surface_old_all, surface_force_all)
    plot_delta_error(surface_ini_all, surface_old_all, surface_force_all, output_force, scores=scores_force)

    print(f"\nDetailed plots/summary saved to {output_force}")
