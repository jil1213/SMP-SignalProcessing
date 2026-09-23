# Plots and summary statistics for the qa_flag==1 similarity scores produced by
# automated_processing_qa1.py: profile-pair similarity before/after alignment,
# pooled across all days and aggregated per day (median), as suggested for the paper.
import calendar
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from scipy.stats import shapiro, wilcoxon, spearmanr

from paper_style import set_paper_style, figsize, C

# Consistent before/after identity across all figures, taken from the paper's own
# color scheme (paper_style.C, matches fig_workflow2.tex) for visual consistency.
COLOR_BEFORE = C["mainblue"]
COLOR_AFTER = C["mainorange"]

# Matplotlib's own boxplot defaults draw the median in orange (C1) on a blue (C0)
# box, which disappears against COLOR_BEFORE/COLOR_AFTER above. Black is the
# conventional, print-safe choice that stays legible against both.
MEDIAN_COLOR = "black"
BOX_STYLE_KWARGS = dict(
    medianprops=dict(color=MEDIAN_COLOR, linewidth=1.4),
    flierprops=dict(marker="o", markersize=3, markeredgewidth=0.5),
)


def load_scores(csv_path):
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["folder"], format="%Y%m%d")
    return df


def plot_pooled_boxplot(df, output_dir):
    # matplotlib's boxplot does not drop NaNs on its own (a handful of pairs have no
    # valid overlap after alignment) - would otherwise silently render an empty box.
    with plt.rc_context():
        set_paper_style(usetex=False)
        fig, ax = plt.subplots(figsize=figsize("text", aspect=85 / 177))
        ax.boxplot([df["similarity_before"].dropna(), df["similarity_after"].dropna()],
                   labels=["Before alignment", "After alignment"], **BOX_STYLE_KWARGS)
        ax.set_ylabel("Cosine similarity")
        ax.grid()
        plt.savefig(output_dir / "similarity_boxplot_pooled.png", dpi=300)
        plt.savefig(output_dir / "similarity_boxplot_pooled.pdf")
        plt.close()


def plot_daily_median(df, output_dir):
    # S_tilde_d = median_{i<j} S_ij per day, computed separately before/after alignment
    daily = df.groupby("date")[["similarity_before", "similarity_after"]].median().reset_index()

    with plt.rc_context():
        set_paper_style(usetex=False)
        fig, ax = plt.subplots(figsize=figsize("text", aspect=85 / 177))
        ax.scatter(daily["date"], daily["similarity_before"], s=10, marker="o",
                   color=COLOR_BEFORE, alpha=0.7, linewidths=0, label="Before alignment")
        ax.scatter(daily["date"], daily["similarity_after"], s=10, marker="^",
                   color=COLOR_AFTER, alpha=0.7, linewidths=0, label="After alignment")
        ax.set_xlabel("Date")
        ax.set_ylabel(r"Daily median similarity $\tilde{S}_d$")
        ax.grid()
        ax.legend(fontsize="small")
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        plt.savefig(output_dir / "similarity_daily_median.png", dpi=300)
        plt.savefig(output_dir / "similarity_daily_median.pdf")
        plt.close()

    return daily


def plot_before_after_scatter(df, output_dir):
    with plt.rc_context():
        set_paper_style(usetex=False)
        fig, ax = plt.subplots(figsize=figsize(90, aspect=1.0))
        ax.scatter(df["similarity_before"], df["similarity_after"], s=4, alpha=0.25,
                   color=COLOR_BEFORE, linewidths=0)
        lims = [0, 1]
        ax.plot(lims, lims, color="grey", linestyle="--", linewidth=0.8, zorder=0, label="y = x")
        ax.set_xlim(lims)
        ax.set_ylim(lims)
        ax.set_xlabel("Similarity before alignment")
        ax.set_ylabel("Similarity after alignment")
        ax.set_aspect("equal")
        ax.grid()
        ax.legend(fontsize="small")
        plt.savefig(output_dir / "similarity_scatter_before_after.png", dpi=300)
        plt.savefig(output_dir / "similarity_scatter_before_after.pdf")
        plt.close()


def plot_delta_distribution(df, output_dir):
    # Delta S = S_after - S_before per pair, same single-box style as delta_error_boxplot.py
    delta = (df["similarity_after"] - df["similarity_before"]).dropna()
    with plt.rc_context():
        set_paper_style(usetex=False)
        fig, ax = plt.subplots(figsize=figsize(90, aspect=85 / 90))
        ax.boxplot([delta], labels=[r"$\Delta S$ (after $-$ before)"], **BOX_STYLE_KWARGS)
        ax.axhline(0, color="grey", linestyle="--", linewidth=0.8, zorder=0)
        ax.set_ylabel(r"$\Delta S$")
        ax.grid()
        plt.savefig(output_dir / "similarity_delta_boxplot.png", dpi=300)
        plt.savefig(output_dir / "similarity_delta_boxplot.pdf")
        plt.close()
    return delta


def plot_offset_histogram(df, output_dir):
    with plt.rc_context():
        set_paper_style(usetex=False)
        fig, ax = plt.subplots(figsize=figsize("text", aspect=75 / 177))
        ax.hist(df["offset_mm"], bins=60, color=COLOR_BEFORE, edgecolor="white", linewidth=0.3)
        ax.axvline(0, color="grey", linestyle="--", linewidth=0.8, zorder=0)
        ax.set_xlabel("Alignment offset (mm)")
        ax.set_ylabel("Number of pairs")
        ax.grid()
        plt.savefig(output_dir / "similarity_offset_histogram.png", dpi=300)
        plt.savefig(output_dir / "similarity_offset_histogram.pdf")
        plt.close()


def plot_offset_vs_delta(df, output_dir):
    # Does a larger necessary shift correspond to a larger similarity gain?
    valid = df.dropna(subset=["similarity_after"])
    delta = valid["similarity_after"] - valid["similarity_before"]
    with plt.rc_context():
        set_paper_style(usetex=False)
        fig, ax = plt.subplots(figsize=figsize(90, aspect=85 / 90))
        ax.scatter(valid["offset_mm"].abs(), delta, s=4, alpha=0.25, color=COLOR_AFTER, linewidths=0)
        ax.axhline(0, color="grey", linestyle="--", linewidth=0.8, zorder=0)
        ax.set_xlabel("Absolute alignment offset (mm)")
        ax.set_ylabel(r"$\Delta S$")
        ax.grid()
        plt.savefig(output_dir / "similarity_offset_vs_delta.png", dpi=300)
        plt.savefig(output_dir / "similarity_offset_vs_delta.pdf")
        plt.close()


def plot_seasonal_boxplot(df, daily, output_dir):
    # Daily medians S_tilde_d grouped by calendar month (pooled across all years),
    # restricted to the snow season Nov-May and ordered so it runs Nov, Dec, Jan, ...,
    # May instead of the calendar's Jan-first order.
    daily = daily.copy()
    daily["month"] = daily["date"].dt.month
    season_months = [11, 12, 1, 2, 3, 4, 5]

    # Profile-pair counts (per-pair rows, not per-day medians) per month, for the n= labels
    n_pairs_per_month = df.assign(month=df["date"].dt.month).groupby("month").size()

    rows = []
    for pos, m in enumerate(season_months, start=1):
        before_vals = daily.loc[daily["month"] == m, "similarity_before"].dropna().values
        after_vals = daily.loc[daily["month"] == m, "similarity_after"].dropna().values
        if len(before_vals) > 0 and len(after_vals) > 0:
            rows.append((pos, m, before_vals, after_vals))
    positions, months, before_by_month, after_by_month = zip(*rows)

    positions_before = [p - 0.18 for p in positions]
    positions_after = [p + 0.18 for p in positions]

    with plt.rc_context():
        set_paper_style(usetex=False)
        fig, ax = plt.subplots(figsize=figsize("text", aspect=85 / 177))
        bp_before = ax.boxplot(before_by_month, positions=positions_before, widths=0.32,
                                patch_artist=True, manage_ticks=False, **BOX_STYLE_KWARGS)
        bp_after = ax.boxplot(after_by_month, positions=positions_after, widths=0.32,
                               patch_artist=True, manage_ticks=False, **BOX_STYLE_KWARGS)
        for box in bp_before["boxes"]:
            box.set_facecolor(COLOR_BEFORE)
            box.set_alpha(0.6)
        for box in bp_after["boxes"]:
            box.set_facecolor(COLOR_AFTER)
            box.set_alpha(0.6)

        ax.set_xticks(list(positions))
        ax.set_xticklabels([f"{calendar.month_abbr[m]}\n(n={int(n_pairs_per_month.get(m, 0))})"
                             for m in months])
        ax.set_ylim(0, 1)
        ax.set_ylabel(r"Daily median similarity $\tilde{S}_d$")
        ax.legend([bp_before["boxes"][0], bp_after["boxes"][0]],
                  ["Before alignment", "After alignment"], fontsize="small")
        ax.grid()
        plt.savefig(output_dir / "similarity_seasonal_boxplot.png", dpi=300)
        plt.savefig(output_dir / "similarity_seasonal_boxplot.pdf")
        plt.close()


def plot_extreme_pairs(df, repo_root, output_dir, n_pairs=20):
    # Re-loads the raw profiles for the most extreme pairs (worst and best, by two
    # criteria) and re-runs the existing get_offset/align_profiles plotting
    # (plot=True) to inspect what happened. Each pair is saved into one or more
    # criterion subfolders, depending on which selection(s) it belongs to.
    from code_pipeline_additional.automated_processing_qa1 import load_profiles_qa1
    from code_automated_correlation.a_automated_processing import get_offset, align_profiles

    valid = df.dropna(subset=["similarity_after"]).copy()
    valid["delta"] = valid["similarity_after"] - valid["similarity_before"]

    pair_cols = ["folder", "profile_name_1", "profile_name_2"]
    selections = {
        "worst_delta": valid.nsmallest(n_pairs, "delta"),
        "worst_similarity_after": valid.nsmallest(n_pairs, "similarity_after"),
        "best_delta": valid.nlargest(n_pairs, "delta"),
        "best_similarity_after": valid.nlargest(n_pairs, "similarity_after"),
    }
    keys_by_selection = {name: set(map(tuple, sel[pair_cols].values)) for name, sel in selections.items()}

    outlier_dir = output_dir / "outliers"
    target_dirs = {name: outlier_dir / name for name in selections}
    for d in target_dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    candidates = pd.concat(selections.values()).drop_duplicates(subset=pair_cols)
    raw_data_root = repo_root / "code_automated_correlation" / "raw_data"

    for folder_name, group in candidates.groupby("folder"):
        folder_path = raw_data_root / str(folder_name)
        smp_profiles = load_profiles_qa1(folder_path)
        for _, row in group.iterrows():
            name1, name2 = row["profile_name_1"], row["profile_name_2"]
            if name1 not in smp_profiles or name2 not in smp_profiles:
                continue
            df1, df2 = smp_profiles[name1], smp_profiles[name2]
            key = (row["folder"], name1, name2)
            dirs_for_pair = [target_dirs[name] for name, keys in keys_by_selection.items() if key in keys]

            date_str = row["date"].strftime("%Y-%m-%d")
            sim_before, sim_after = row["similarity_before"], row["similarity_after"]
            for target_dir in dirs_for_pair:
                _, _, lag = get_offset(df1, df2, name1, name2, plot=True, target_dir=target_dir,
                                        date_str=date_str, sim_before=sim_before, sim_after=sim_after)
                align_profiles(df1, df2, name1, name2, lag, plot=True, target_dir=target_dir,
                                date_str=date_str, sim_before=sim_before, sim_after=sim_after)

    summary = ", ".join(f"{len(sel)} {name}" for name, sel in selections.items())
    print(f"Extreme pair plots ({summary}, {len(candidates)} unique pairs) saved to: {outlier_dir}")
    return candidates


def save_summary(df, daily, outliers, output_dir):
    delta_all = df["similarity_after"] - df["similarity_before"]
    valid = df.dropna(subset=["similarity_after"])
    delta = valid["similarity_after"] - valid["similarity_before"]

    stat_shapiro, p_shapiro = shapiro(delta)
    stat_wilcoxon, p_wilcoxon = wilcoxon(valid["similarity_before"], valid["similarity_after"])
    corr, p_corr = spearmanr(valid["offset_mm"].abs(), delta)

    lines = [
        f"n pairs: {len(df)}",
        f"n days: {df['folder'].nunique()}",
        f"n pairs with failed alignment (similarity_after = NaN): {df['similarity_after'].isna().sum()}",
        "",
        "Pooled (all pairs, all days):",
        f"  median before = {df['similarity_before'].median():.4f}",
        f"  median after  = {df['similarity_after'].median():.4f}",
        f"  mean before   = {df['similarity_before'].mean():.4f}",
        f"  mean after    = {df['similarity_after'].mean():.4f}",
        f"  median delta S (after - before) = {delta_all.median():.4f}",
        f"  mean delta S   (after - before) = {delta_all.mean():.4f}",
        f"  share of pairs improved (delta S > 0) = {(delta_all > 0).mean():.2%}",
        "",
        "Daily medians S_tilde_d (median_{i<j} S_ij per day):",
        f"  median of daily medians, before = {daily['similarity_before'].median():.4f}",
        f"  median of daily medians, after  = {daily['similarity_after'].median():.4f}",
        "",
        f"Paired significance test on delta S (n = {len(valid)}):",
        f"  Shapiro-Wilk on delta S: stat={stat_shapiro:.4f}, p={p_shapiro:.2e} "
        f"({'not normal -> use non-parametric test' if p_shapiro < 0.05 else 'looks normal'})",
        f"  Wilcoxon signed-rank test (before vs after): stat={stat_wilcoxon:.1f}, p={p_wilcoxon:.2e}",
        "",
        "Alignment offset:",
        f"  median |offset| = {valid['offset_mm'].abs().median():.3f} mm",
        f"  mean |offset|   = {valid['offset_mm'].abs().mean():.3f} mm",
        f"  Spearman correlation |offset_mm| vs delta S: rho={corr:.3f}, p={p_corr:.2e}",
        "",
        f"Extreme diagnostic pairs plotted (worst/best delta S and/or S_after): {len(outliers)}",
    ]
    (output_dir / "similarity_summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    csv_path = script_dir / "output" / "similarity_scores_qa1.csv"
    output_dir = script_dir / "output"

    df = load_scores(csv_path)
    plot_pooled_boxplot(df, output_dir)
    daily = plot_daily_median(df, output_dir)
    plot_before_after_scatter(df, output_dir)
    plot_delta_distribution(df, output_dir)
    plot_offset_histogram(df, output_dir)
    plot_offset_vs_delta(df, output_dir)
    plot_seasonal_boxplot(df, daily, output_dir)
    outliers = plot_extreme_pairs(df, repo_root, output_dir)
    save_summary(df, daily, outliers, output_dir)

    print(f"\nPlots and summary saved to: {output_dir}")
