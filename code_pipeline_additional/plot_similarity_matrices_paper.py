# Paper-only visualizations of similarity matrices for 5 selected days.
# Not part of the regular processing pipeline - safe to delete once the paper is done.
#
# Produces:
#   - one figure with the two speed-test days (20250131_T, 20250321_T) side by side
#   - one figure with the three "free" days (20160127, 20191229, 20250403) side by side,
#     using the same color scale/colorbar/style as the speed-test-day figure
#   - exact median/IQR of the pooled off-diagonal values of all 5 matrices (as text)
#   - per speed-test day, a figure with the velocity=20mm/s and velocity=8mm/s
#     sub-matrices side by side (same style/color scale as above)
#   - exact median/quartile/range statistics of the velocity sub-matrices (unrounded),
#     plus the raw unrounded pairwise similarity scores, as text/csv
import pickle

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from datetime import datetime

from code_automated_correlation.a_automated_processing import load_profiles
from code_automated_correlation.b_automated_similarity import compute_aligned_similarity_matrix
from paper_style import set_paper_style, figsize

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
RAW_DATA_DIR = REPO_ROOT / "code_automated_correlation" / "raw_data"
ALLOCATION_XLSX = REPO_ROOT / "data" / "smp_allocation.xlsx"

OUTPUT_DIR = SCRIPT_DIR / "output" / "similarity_matrices_paper"
CACHE_DIR = OUTPUT_DIR / "cache"

SPEEDTEST_DAYS = ["20250131_T", "20250321_T"]
FREE_DAYS = ["20160127", "20191229", "20250403"]
ALL_DAYS = SPEEDTEST_DAYS + FREE_DAYS

# Site names for the two datasets, used instead of raw folder/date strings in figure
# titles, filenames and stats output (WFJ = Weissfluhjoch, the "free" days; Tyrol =
# the two dedicated speed-test days).
SITE_OF_DAY = {
    "20160127": "WFJ 1", "20191229": "WFJ 2", "20250403": "WFJ 3",
    "20250131_T": "Tyrol 1", "20250321_T": "Tyrol 2",
}
SITE_SLUG = {  # for filenames
    "20160127": "wfj1", "20191229": "wfj2", "20250403": "wfj3",
    "20250131_T": "tyrol1", "20250321_T": "tyrol2",
}

# Velocity (mm/s) -> profile name, per speed-test day. Taken from data/smp_allocation.xlsx,
# which is the authoritative manual record of which profile was measured at which speed
# (this metadata is not stored in the .PNT/.ini files themselves).
SPEEDTEST_DAY_TO_ALLOCATION_DATE = {"20250131_T": 1, "20250321_T": 2}

VMIN, VMAX = 0.0, 1.0
CMAP = "coolwarm"


def day_label(day):
    clean = day.replace("_T", "")
    return datetime.strptime(clean, "%Y%m%d").strftime("%Y-%m-%d")


def f_labels(n):
    return [f"F{i + 1}" for i in range(n)]


def get_day_matrix(day, use_cache=True):
    """Loads (or computes and caches) the full aligned cosine-similarity matrix for one
    raw_data day-folder, profiles sorted by name (= chronological order for these serials)."""
    cache_file = CACHE_DIR / f"{day}.pkl"
    if use_cache and cache_file.exists():
        with open(cache_file, "rb") as f:
            data = pickle.load(f)
        return pd.DataFrame(data["matrix"], index=data["labels"], columns=data["labels"])

    print(f"Computing similarity matrix for {day} ...")
    profiles = load_profiles(RAW_DATA_DIR / day)
    profiles = {name: profiles[name] for name in sorted(profiles)}
    corr_df = compute_aligned_similarity_matrix(profiles, day, save=False)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "wb") as f:
        pickle.dump({"labels": list(corr_df.index), "matrix": corr_df.values}, f)
    return corr_df


def load_velocity_allocation():
    """name -> velocity (mm/s) for the profiles of the two speed-test days."""
    allocation = pd.read_excel(ALLOCATION_XLSX)
    allocation = allocation[allocation["velocity"].isin([8, 20])]
    return dict(zip(allocation["name"], allocation["velocity"]))


def off_diagonal_values(corr_df):
    """The M*(M-1)/2 unique off-diagonal similarity values of a matrix."""
    m = corr_df.values
    iu = np.triu_indices(len(m), k=1)
    return m[iu]


def plot_matrix_row(corr_dfs, titles, output_path, value_fontsize=5.5, title_loc="center"):
    n = len(corr_dfs)
    with plt.rc_context():
        set_paper_style(usetex=False)
        fig, axes = plt.subplots(1, n, figsize=figsize("text", aspect=0.40 / n * n ** 0.55))
        axes = np.atleast_1d(axes)

        im = None
        for ax, corr_df, title, letter in zip(axes, corr_dfs, titles, "abcdefghij"):
            m = corr_df.values
            labels = f_labels(len(corr_df))
            im = ax.imshow(m, vmin=VMIN, vmax=VMAX, cmap=CMAP)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=90)
            ax.set_yticks(range(len(labels)))
            ax.set_yticklabels(labels)
            ax.tick_params(length=0)
            for i in range(len(labels)):
                for j in range(len(labels)):
                    color = "white" if abs(m[i, j] - 0.5) > 0.25 else "black"
                    ax.text(j, i, f"{m[i, j]:.2f}", ha="center", va="center",
                             fontsize=value_fontsize, color=color)
            panel_title = f"({letter}) {title}" if title else f"({letter})"
            ax.set_title(panel_title, loc=title_loc)

        cbar = fig.colorbar(im, ax=list(axes), shrink=0.85)
        cbar.set_label("Inter-profile similarity")
        plt.savefig(output_path.with_suffix(".png"), dpi=300)
        plt.savefig(output_path.with_suffix(".pdf"))
        plt.close()


def save_pooled_median_iqr(day_matrices, output_path):
    pooled = np.concatenate([off_diagonal_values(day_matrices[d]) for d in ALL_DAYS])
    q1, median, q3 = np.percentile(pooled, [25, 50, 75])

    lines = [
        "Median / IQR of the off-diagonal similarity values, per dataset and pooled",
        "(WFJ 1-3 = the three free days; Tyrol 1-2 = the two speed-test days)",
        "",
        "Per dataset (all M*(M-1)/2 off-diagonal values of that dataset's matrix, unrounded):",
    ]
    for d in ALL_DAYS:
        values = off_diagonal_values(day_matrices[d])
        dq1, dmedian, dq3 = np.percentile(values, [25, 50, 75])
        lines.append(
            f"  {SITE_OF_DAY[d]} ({day_label(d)}): M={len(day_matrices[d])}, n={len(values)} "
            f"-> median={dmedian:.4f}  IQR={dq3 - dq1:.4f}  (Q1={dq1:.4f}, Q3={dq3:.4f})"
        )
    lines += [
        "",
        f"Pooled across all 5 datasets (n={len(pooled)} values):",
        f"  Median (exact, unrounded)       = {median!r}",
        f"  Q1 (25th percentile, unrounded) = {q1!r}",
        f"  Q3 (75th percentile, unrounded) = {q3!r}",
        f"  IQR (Q3 - Q1, unrounded)        = {q3 - q1!r}",
        "",
        f"  Median (4 decimals) = {median:.4f}",
        f"  Q1 (4 decimals)     = {q1:.4f}",
        f"  Q3 (4 decimals)     = {q3:.4f}",
        f"  IQR (4 decimals)    = {q3 - q1:.4f}",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def speed_submatrices(day_matrix, velocity_of):
    names_20 = [n for n in day_matrix.index if velocity_of.get(n) == 20]
    names_8 = [n for n in day_matrix.index if velocity_of.get(n) == 8]
    return day_matrix.loc[names_20, names_20], day_matrix.loc[names_8, names_8]


def save_speed_comparison_stats(speed_data, output_path_txt, output_path_csv):
    """speed_data: {day: {20: sub_df, 8: sub_df}}"""
    rows = []
    for day, groups in speed_data.items():
        for velocity, sub_df in groups.items():
            names = list(sub_df.index)
            for i, n1 in enumerate(names):
                for j, n2 in enumerate(names):
                    if i < j:
                        rows.append({
                            "dataset": SITE_OF_DAY[day],
                            "day": day,
                            "velocity_mm_s": velocity,
                            "profile_1": n1,
                            "profile_2": n2,
                            "cosine_similarity": sub_df.loc[n1, n2],
                        })
    raw_df = pd.DataFrame(rows)
    raw_df.to_csv(output_path_csv, index=False)

    def stats_block(values, label):
        values = np.asarray(values, dtype=float)
        q1, median, q3 = np.percentile(values, [25, 50, 75])
        return [
            f"{label}: n={len(values)}",
            f"  median (unrounded) = {median!r}",
            f"  Q1 (unrounded)     = {q1!r}",
            f"  Q3 (unrounded)     = {q3!r}",
            f"  IQR (unrounded)    = {q3 - q1!r}",
            f"  min (unrounded)    = {values.min()!r}",
            f"  max (unrounded)    = {values.max()!r}",
            f"  range (unrounded)  = {values.max() - values.min()!r}",
            f"  median={median:.4f}  Q1={q1:.4f}  Q3={q3:.4f}  IQR={q3 - q1:.4f}  "
            f"min={values.min():.4f}  max={values.max():.4f}  range={values.max() - values.min():.4f}",
        ]

    lines = ["Median / quartile / range statistics of the velocity sub-matrices",
             "(recomputed from the unrounded cosine-similarity values, not the rounded",
             "numbers used in the master's thesis).", ""]
    for day, groups in speed_data.items():
        lines.append(f"--- {SITE_OF_DAY[day]} ({day_label(day)}) ---")
        for velocity in (20, 8):
            values = off_diagonal_values(groups[velocity])
            lines += stats_block(values, f"velocity = {velocity} mm/s")
        lines.append("")

    lines.append("--- pooled across both speed-test days ---")
    for velocity in (20, 8):
        pooled_values = raw_df.loc[raw_df["velocity_mm_s"] == velocity, "cosine_similarity"].values
        lines += stats_block(pooled_values, f"velocity = {velocity} mm/s")

    output_path_txt.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- load / compute the 5 day matrices (speed-test days processed first, in order) ---
    day_matrices = {}
    for day in ALL_DAYS:
        day_matrices[day] = get_day_matrix(day)

    # --- Figure 1: the two speed-test days (Tyrol), side by side, panel letter only, left-aligned ---
    plot_matrix_row(
        [day_matrices[d] for d in SPEEDTEST_DAYS],
        ["" for _ in SPEEDTEST_DAYS],
        OUTPUT_DIR / "fig_similarity_matrix_tyrol",
        title_loc="left",
    )

    # --- Figure 2: the three free days (WFJ), side by side, same style/colorbar, panel letter only, left-aligned ---
    plot_matrix_row(
        [day_matrices[d] for d in FREE_DAYS],
        ["" for _ in FREE_DAYS],
        OUTPUT_DIR / "fig_similarity_matrix_wfj",
        title_loc="left",
    )

    # --- exact median/IQR of the pooled off-diagonal values of all 5 matrices ---
    save_pooled_median_iqr(day_matrices, OUTPUT_DIR / "similarity_matrix_median_iqr.txt")

    # --- speed-test sub-matrices (velocity = 20 mm/s vs 8 mm/s), per day ---
    velocity_of = load_velocity_allocation()
    speed_data = {}
    for day in SPEEDTEST_DAYS:
        sub_20, sub_8 = speed_submatrices(day_matrices[day], velocity_of)
        speed_data[day] = {20: sub_20, 8: sub_8}
        plot_matrix_row(
            [sub_20, sub_8],
            ["20 mm/s", "8 mm/s"],
            OUTPUT_DIR / f"fig_similarity_matrix_speed_comparison_{SITE_SLUG[day]}",
        )

    save_speed_comparison_stats(
        speed_data,
        OUTPUT_DIR / "speed_comparison_stats.txt",
        OUTPUT_DIR / "speed_comparison_raw_scores.csv",
    )

    print(f"\nAll paper figures and stats saved to: {OUTPUT_DIR}")
