# Sweeps the k factor (and whether air_force_mean is included) of the
# force_threshold used inside detect_surface, to find the combination that
# minimizes the number of boxplot outliers of delta = surface_new - surface_ini.
import numpy as np
import pandas as pd
import configparser
import matplotlib.pyplot as plt

from pathlib import Path
from snowmicropyn import Profile
from snowmicropyn.tools import smooth
from sklearn.metrics import mean_absolute_error, mean_squared_error
from code_SMP.detect_surface import detect_surface, moving_linear_regression
from paper_style import set_paper_style, figsize

plt.style.use(Path(__file__).resolve().parent.parent / 'latex_default.mplstyle')


def load_profiles(folder_path):
    # same loading/filtering logic as tune_surfacedetection.py (qa_flag == 1, needs surface_ini)
    # additionally runs detect_surface once per profile just to get its "precomputed" tuple
    # (gradient + air stats), so the k/use_air_mean sweep below doesn't redo that expensive part
    # for every combination.
    profiles = []
    pnt_files = folder_path.rglob("*.PNT")

    for file in pnt_files:
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
            continue  # no manual reference -> can't score this profile

        smp_profile = Profile.load(file)
        df = smp_profile.samples
        name = smp_profile.name

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

        precomputed = (distance, force, grad, threshold, air_force_mean, air_force_std)
        profiles.append((name, precomputed, surface_ini))

    return profiles


def outlier_counts(delta):
    # same 1.5*IQR rule as the boxplot in tune_surfacedetection.py's plot_delta_error
    q1, q3 = np.percentile(delta, [25, 75])
    iqr = q3 - q1
    lf, hf = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_below = int(np.sum(delta < lf))
    n_above = int(np.sum(delta > hf))
    return n_below, n_above


if __name__ == "__main__":
    folder_path = Path("surfacedetection_tuning/test_data3")

    profiles = load_profiles(folder_path)
    print(f"Loaded {len(profiles)} profiles with a manual surface_ini reference.")

    k_values = np.arange(0.5, 6.0 + 1e-9, 0.25)
    use_air_mean_variants = (True, False)

    rows = []
    for use_air_mean in use_air_mean_variants:
        for k in k_values:
            surface_ini_all = []
            surface_new_all = []
            for name, precomputed, surface_ini in profiles:
                surface_new, grad, threshold = detect_surface(
                    None, name, k=k, use_air_mean=use_air_mean, precomputed=precomputed
                )
                surface_ini_all.append(surface_ini)
                surface_new_all.append(surface_new)

            surface_ini_all = np.array(surface_ini_all)
            surface_new_all = np.array(surface_new_all)
            delta = surface_new_all - surface_ini_all

            mae = mean_absolute_error(surface_ini_all, surface_new_all)
            rmse = np.sqrt(mean_squared_error(surface_ini_all, surface_new_all))
            n_below, n_above = outlier_counts(delta)

            rows.append(dict(
                use_air_mean=use_air_mean,
                k=k,
                mae=mae,
                rmse=rmse,
                n_outliers_below=n_below,
                n_outliers_above=n_above,
                n_outliers_total=n_below + n_above,
            ))
            print(f"use_air_mean={use_air_mean}, k={k:.2f} -> "
                  f"MAE={mae:.2f} mm, RMSE={rmse:.2f} mm, outliers={n_below + n_above}")

    results = pd.DataFrame(rows)
    results.to_csv(folder_path / "force_threshold_tuning_results.csv", index=False)

    # Best k per variant: minimize outlier count first, break ties with RMSE
    for use_air_mean, group in results.groupby("use_air_mean"):
        best = group.sort_values(["n_outliers_total", "rmse"]).iloc[0]
        label = "with air_force_mean" if use_air_mean else "without air_force_mean"
        print(
            f"Best k {label}: k={best['k']:.2f} -> "
            f"outliers={int(best['n_outliers_total'])} "
            f"(below={int(best['n_outliers_below'])}, above={int(best['n_outliers_above'])}), "
            f"MAE={best['mae']:.2f} mm, RMSE={best['rmse']:.2f} mm"
        )

    overall_best = results.sort_values(["n_outliers_total", "rmse"]).iloc[0]
    variant_label = "with air_force_mean" if overall_best["use_air_mean"] else "without air_force_mean"
    print(
        f"\nOverall best: k={overall_best['k']:.2f}, {variant_label} -> "
        f"outliers={int(overall_best['n_outliers_total'])}, "
        f"MAE={overall_best['mae']:.2f} mm, RMSE={overall_best['rmse']:.2f} mm"
    )

    # Plot outlier count and RMSE vs k for both variants
    variant_labels = {True: "with air_force_mean", False: "without air_force_mean"}
    with plt.rc_context():
        set_paper_style(usetex=False)
        fig, (ax_outliers, ax_rmse) = plt.subplots(1, 2, figsize=figsize("text", aspect=85 / 177))

        for use_air_mean, group in results.groupby("use_air_mean"):
            group = group.sort_values("k")
            ax_outliers.plot(group["k"], group["n_outliers_total"], marker='o', markersize=3,
                              label=variant_labels[use_air_mean])
            ax_rmse.plot(group["k"], group["rmse"], marker='o', markersize=3,
                         label=variant_labels[use_air_mean])

        ax_outliers.set_xlabel("k")
        ax_outliers.set_ylabel("Number of boxplot outliers")
        ax_outliers.grid()
        ax_outliers.legend()

        ax_rmse.set_xlabel("k")
        ax_rmse.set_ylabel("RMSE (mm)")
        ax_rmse.grid()
        ax_rmse.legend()

        plt.savefig(folder_path / "force_threshold_tuning.png", dpi=300)
        plt.savefig(folder_path / "force_threshold_tuning.pdf")
        plt.close()

    print(f"\nFull results saved to {folder_path / 'force_threshold_tuning_results.csv'}")
    print(f"Sweep plot saved to {folder_path / 'force_threshold_tuning.png'} / .pdf")
