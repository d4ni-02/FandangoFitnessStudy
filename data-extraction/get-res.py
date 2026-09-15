#!/usr/bin/env python3
"""
Ablation study analysis for the FANDANGO fuzzer.

Scans a directory (default: the current working directory) for CSV files
produced by FANDANGO and aggregates them into ablation-friendly metrics.

Recognised files
----------------
Summary (one file per run, multiple rows: one per subject):
    evaluation_summary_results_run<N>.csv

Generations (one file per subject and run):
    ablation_generations_<subject>_<duration>s_run<N>.csv

The experimental condition is inferred from the directory name:
    csv-tests-Linear       -> "linear"
    csv-tests-Exponential  -> "exp"
Any other suffix is lowercased and used as-is.

Outputs (written to the current working directory)
--------------------------------------------------
    valid_percentage_aggregate.csv
    grammar_coverage_aggregate.csv
    efficiency_aggregate.csv
    fitness_vs_generation.csv
    valid_count_vs_generation.csv
    final_metrics_aggregate.csv
    statistical_tests.csv
    plots/*.png

Analyses included
-----------------
1.  Mean and median fitness vs generation
2.  Std of fitness vs generation
3.  Valid solutions count vs generation
8.  Efficiency: valid solutions per second and per input
10. Statistical comparison between conditions (Mann-Whitney U)

Usage
-----
    # scan the current directory
    python analyze_ablation.py

    # scan a specific directory
    python analyze_ablation.py --dir /path/to/csv-tests-Linear
"""

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------------------
# File patterns
# ---------------------------------------------------------------------------
SUMMARY_GLOB     = "../csv-tests-Linear/evaluation_summary_results_run*.csv"
GENERATIONS_GLOB = "../csv-tests-Linear/ablation_generations_*_run*.csv"

SUBJECT_PATTERNS = {
    "Test1": re.compile(r"person", re.IGNORECASE),
    "Test2":   re.compile(r"math",   re.IGNORECASE),
    "Test3":   re.compile(r"byte",   re.IGNORECASE),
}
RUN_ID_PATTERN = re.compile(r"run[_\-]?(\d+)", re.IGNORECASE)

# Directory-name suffix -> canonical condition name
CONDITION_ALIASES = {
    "linear":      "linear",
    "exponential": "exp",
    "exp":         "exp",
    "quadratic":   "quadratic",
    "log":         "log",
}


def infer_subject(path: Path):
    """Return PERSON / Math / BYTE from the filename, or None."""
    for subj, pat in SUBJECT_PATTERNS.items():
        if pat.search(path.name):
            return subj
    return None


def infer_run_id(path: Path) -> str:
    """Return a run identifier such as 'run1' from the filename."""
    m = RUN_ID_PATTERN.search(path.stem)
    return f"run{m.group(1)}" if m else path.stem


def infer_condition_from_dir(directory: Path) -> str:
    """
    Infer condition from the folder name, e.g. 'csv-tests-Linear' -> 'linear'.
    Falls back to the lowercased directory name if nothing matches.
    """
    name = directory.name.lower()
    for key, canonical in CONDITION_ALIASES.items():
        if key in name:
            return canonical
    return name


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_summaries(paths, condition: str) -> pd.DataFrame:
    """
    Load every summary CSV into one long DataFrame.
    Each summary file already contains a `subject` column (PERSON / Math / BYTE),
    so we do not need to infer it from the filename.
    """
    frames = []
    for f in paths:
        df = pd.read_csv(f)
        df["condition"]   = condition
        df["run_id"]      = infer_run_id(f)
        df["source_file"] = f.name
        frames.append(df)
    if not frames:
        raise FileNotFoundError("No summary files found.")
    return pd.concat(frames, ignore_index=True)


def load_generations(paths, condition: str) -> pd.DataFrame:
    """Load every per-generation CSV into one long DataFrame."""
    frames = []
    for f in paths:
        subj = infer_subject(f)
        if subj is None:
            print(f"[warn] cannot infer subject from {f.name}, skipping")
            continue
        df = pd.read_csv(f)
        df["subject"]   = subj
        df["condition"] = condition
        df["run_id"]    = infer_run_id(f)
        df["source_file"] = f.name
        # Drop the heavy per-individual fitness list; not needed here.
        if "gen_fitness_vals" in df.columns:
            df = df.drop(columns=["gen_fitness_vals"])
        frames.append(df)
    if not frames:
        raise FileNotFoundError("No generation files found.")
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Descriptive aggregation helper
# ---------------------------------------------------------------------------
def _stats(series: pd.Series) -> pd.Series:
    return pd.Series({
        "n_runs": series.count(),
        "mean":   series.mean(),
        "std":    series.std(),
        "median": series.median(),
        "q25":    series.quantile(0.25),
        "q75":    series.quantile(0.75),
        "min":    series.min(),
        "max":    series.max(),
    })


# ---------------------------------------------------------------------------
# Aggregations
# ---------------------------------------------------------------------------
def aggregate_valid_percentage(summary: pd.DataFrame) -> pd.DataFrame:
    return (
        summary.groupby(["condition", "subject"])["valid_percentage"]
        .apply(_stats).unstack().reset_index()
    )


def aggregate_grammar_coverage(summary: pd.DataFrame) -> pd.DataFrame:
    summary = summary.copy()
    summary["coverage"] = summary["covered_rules"] / summary["total_rules"]
    return (
        summary.groupby(["condition", "subject"])["coverage"]
        .apply(_stats).unstack().reset_index()
    )


def aggregate_efficiency(summary: pd.DataFrame) -> pd.DataFrame:
    """Valid solutions per second and per input (throughput metrics)."""
    s = summary.copy()
    s["valid_per_second"] = s["valid_solutions"] / s["run_time_seconds"]
    s["valid_per_input"]  = s["valid_solutions"] / s["total_inputs"]
    return (
        s.groupby(["condition", "subject"])
        .agg(
            valid_per_second_mean=("valid_per_second", "mean"),
            valid_per_second_std =("valid_per_second", "std"),
            valid_per_input_mean =("valid_per_input",  "mean"),
            valid_per_input_std  =("valid_per_input",  "std"),
            n_runs               =("valid_per_second", "count"),
        )
        .reset_index()
    )


def aggregate_fitness_vs_generation(gen: pd.DataFrame) -> pd.DataFrame:
    agg = (
        gen.groupby(["condition", "subject", "generation"])
        .agg(
            n_runs              =("best_fitness", "count"),
            best_fitness_mean   =("best_fitness", "mean"),
            best_fitness_std    =("best_fitness", "std"),
            best_fitness_median =("best_fitness", "median"),
            mean_fitness_mean   =("mean_fitness", "mean"),
            mean_fitness_median =("mean_fitness", "median"),
            median_fitness_mean =("median_fitness", "mean"),
            std_fitness_mean    =("std_fitness", "mean"),
            std_fitness_std     =("std_fitness", "std"),
        )
        .reset_index()
    )
    agg["best_fitness_ci95"] = (
        1.96 * agg["best_fitness_std"] / np.sqrt(agg["n_runs"].clip(lower=1))
    )
    return agg


def aggregate_valid_count_vs_generation(gen: pd.DataFrame) -> pd.DataFrame:
    return (
        gen.groupby(["condition", "subject", "generation"])
        .agg(
            valid_count_mean=("valid_solutions_count", "mean"),
            valid_count_std =("valid_solutions_count", "std"),
            n_runs          =("valid_solutions_count", "count"),
        )
        .reset_index()
    )


def aggregate_final_table(summary: pd.DataFrame, gen: pd.DataFrame) -> pd.DataFrame:
    """One row per (condition, subject) combining summary and last generation."""
    final_gen = (
        gen.sort_values("generation")
        .groupby(["condition", "subject", "run_id"])
        .tail(1)
    )
    fgen = (
        final_gen.groupby(["condition", "subject"])
        .agg(
            final_best_fitness_mean=("best_fitness", "mean"),
            final_best_fitness_std =("best_fitness", "std"),
            final_mean_fitness_mean=("mean_fitness", "mean"),
            final_valid_count_mean =("valid_solutions_count", "mean"),
            final_fixes_mean       =("fixes_made_so_far", "mean"),
            final_mutations_mean   =("mutations_made_so_far", "mean"),
            final_crossovers_mean  =("crossovers_made_so_far", "mean"),
        )
        .reset_index()
    )
    sm = (
        summary.groupby(["condition", "subject"])
        .agg(
            valid_pct_mean  =("valid_percentage", "mean"),
            valid_pct_std   =("valid_percentage", "std"),
            grammar_cov_mean=("grammar_coverage_score", "mean"),
            grammar_cov_std =("grammar_coverage_score", "std"),
            mean_length     =("mean_length", "mean"),
            median_length   =("median_length", "mean"),
            total_inputs    =("total_inputs", "mean"),
            valid_solutions =("valid_solutions", "mean"),
        )
        .reset_index()
    )
    return sm.merge(fgen, on=["condition", "subject"], how="outer")


def statistical_tests(summary: pd.DataFrame, gen: pd.DataFrame) -> pd.DataFrame:
    """
    For each subject and each pair of conditions, compare:
        - valid_percentage
        - grammar_coverage
        - final best_fitness
    using Mann-Whitney U (independent samples, two-sided).

    If your runs are paired by seed, replace stats.mannwhitneyu with
    stats.wilcoxon and align the two samples by run_id first.
    """
    summary = summary.copy()
    summary["coverage"] = summary["covered_rules"] / summary["total_rules"]

    final_gen = (
        gen.sort_values("generation")
        .groupby(["condition", "subject", "run_id"])
        .tail(1)
        [["condition", "subject", "run_id", "best_fitness"]]
    )

    rows = []
    for subj in sorted(summary["subject"].unique()):
        conditions = sorted(summary[summary.subject == subj]["condition"].unique())
        for i in range(len(conditions)):
            for j in range(i + 1, len(conditions)):
                c1, c2 = conditions[i], conditions[j]

                def add(metric, a, b):
                    if len(a) == 0 or len(b) == 0:
                        return
                    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
                    rows.append({
                        "subject": subj, "metric": metric,
                        "condition_a": c1, "condition_b": c2,
                        "n_a": len(a), "n_b": len(b),
                        "mean_a": a.mean(), "mean_b": b.mean(),
                        "median_a": a.median(), "median_b": b.median(),
                        "U": u, "p_value": p,
                    })

                a = summary[(summary.subject == subj) & (summary.condition == c1)]["valid_percentage"].dropna()
                b = summary[(summary.subject == subj) & (summary.condition == c2)]["valid_percentage"].dropna()
                add("valid_percentage", a, b)

                a = summary[(summary.subject == subj) & (summary.condition == c1)]["coverage"].dropna()
                b = summary[(summary.subject == subj) & (summary.condition == c2)]["coverage"].dropna()
                add("grammar_coverage", a, b)

                a = final_gen[(final_gen.subject == subj) & (final_gen.condition == c1)]["best_fitness"].dropna()
                b = final_gen[(final_gen.subject == subj) & (final_gen.condition == c2)]["best_fitness"].dropna()
                add("final_best_fitness", a, b)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------
def plot_curve(curves: pd.DataFrame, y_col: str, ylabel: str,
               filename_tpl: str, y_ci: str = None) -> None:
    for subj in sorted(curves["subject"].unique()):
        plt.figure(figsize=(10, 5))
        for cond in sorted(curves["condition"].unique()):
            d = curves[(curves.subject == subj) & (curves.condition == cond)]
            if d.empty:
                continue
            plt.plot(d.generation, d[y_col], label=cond)
            if y_ci and y_ci in d.columns:
                plt.fill_between(
                    d.generation,
                    d[y_col] - d[y_ci],
                    d[y_col] + d[y_ci],
                    alpha=0.2,
                )
        plt.xlabel("Generation")
        plt.ylabel(ylabel)
        plt.title(f"{ylabel} - {subj}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(filename_tpl.format(subject=subj), dpi=150)
        plt.close()



def plot_boxplot(summary: pd.DataFrame, value_col: str, title: str,
                 filename: str) -> None:
    subjects = sorted(summary["subject"].unique())
    fig, axes = plt.subplots(1, len(subjects), figsize=(5 * len(subjects), 5))
    if len(subjects) == 1:
        axes = [axes]
    for ax, subj in zip(axes, subjects):
        d = summary[summary.subject == subj]
        groups, labels = [], []
        for cond in sorted(d["condition"].unique()):
            groups.append(d[d.condition == cond][value_col].dropna().values)
            labels.append(cond)

        # Matplotlib >= 3.9 renamed `labels` to `tick_labels`.
        # Try the new name first, fall back for older versions.
        try:
            ax.boxplot(groups, tick_labels=labels)
        except TypeError:
            ax.boxplot(groups, labels=labels)

        ax.set_title(subj)
        ax.set_ylabel(title)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(filename, dpi=150)
    plt.close(fig)







def plot_combined_fitness(fit_curve: pd.DataFrame,
                          filename: str = "combined_fitness.png") -> None:
    """
    Single plot with generation on the x-axis and, for each subject:
        - solid line  : mean fitness averaged over runs
        - dashed line : best fitness averaged over runs

    Colors identify the subject; line style identifies the metric.
    A shaded band around each mean curve shows the 95% CI (only for best,
    where we have a std across runs).
    """
    subjects = sorted(fit_curve["subject"].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, len(subjects)))

    fig, ax = plt.subplots(figsize=(12, 7))

    for color, subj in zip(colors, subjects):
        d = fit_curve[fit_curve.subject == subj].sort_values("generation")
        if d.empty:
            continue

        # Mean fitness (solid)
        ax.plot(d.generation, d["mean_fitness_mean"],
                color=color, linestyle="-", linewidth=2,
                label=f"{subj} - mean fitness")

        # Best fitness (dashed), with 95% CI band
        ax.plot(d.generation, d["best_fitness_mean"],
                color=color, linestyle="--", linewidth=2,
                label=f"{subj} - best fitness")
        if "best_fitness_ci95" in d.columns:
            ax.fill_between(d.generation,
                            d["best_fitness_mean"] - d["best_fitness_ci95"],
                            d["best_fitness_mean"] + d["best_fitness_ci95"],
                            color=color, alpha=0.15)

    ax.set_xlabel("Generation")
    ax.set_ylabel("Fitness")
    ax.set_title("Mean and best fitness vs generation (alpha=1.0)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(filename, dpi=150)
    plt.close(fig)





# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dir", default=".",
        help="Directory containing the CSV files (default: current dir).",
    )
    parser.add_argument(
        "--outdir", default=".",
        help="Directory for outputs (default: current dir).",
    )
    args = parser.parse_args()

    src = Path(args.dir).resolve()
    out = Path(args.outdir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    plots_dir = out / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    # ---- Discover files ----
    summary_files = sorted(src.glob(SUMMARY_GLOB))
    gen_files     = sorted(src.glob(GENERATIONS_GLOB))

    if not summary_files:
        raise FileNotFoundError(f"No summary files matching {SUMMARY_GLOB} in {src}")
    if not gen_files:
        raise FileNotFoundError(f"No generation files matching {GENERATIONS_GLOB} in {src}")

    condition = infer_condition_from_dir(src)
    print(f"[info] source dir : {src}")
    print(f"[info] condition  : {condition}")
    print(f"[info] summaries  : {len(summary_files)} files")
    print(f"[info] generations: {len(gen_files)} files")
    

    # ---- Load ----
    summary = load_summaries(summary_files, condition)
    gen     = load_generations(gen_files, condition)
    print(f"[info] summary rows: {len(summary)}, gen rows: {len(gen)}")
    print(f"[info] subjects    : {sorted(summary.subject.unique())}")

    # ---- Aggregate ----
    valid_agg = aggregate_valid_percentage(summary)
    cov_agg   = aggregate_grammar_coverage(summary)
    eff_agg   = aggregate_efficiency(summary)
    fit_curve = aggregate_fitness_vs_generation(gen)
    vc_curve  = aggregate_valid_count_vs_generation(gen)
    final_tab = aggregate_final_table(summary, gen)
    tests     = statistical_tests(summary, gen)

    # ---- Save CSVs ----
    valid_agg.to_csv(out / "valid_percentage_aggregate.csv", index=False)
    cov_agg.to_csv  (out / "grammar_coverage_aggregate.csv",  index=False)
    eff_agg.to_csv  (out / "efficiency_aggregate.csv",        index=False)
    fit_curve.to_csv(out / "fitness_vs_generation.csv",       index=False)
    vc_curve.to_csv (out / "valid_count_vs_generation.csv",   index=False)
    final_tab.to_csv(out / "final_metrics_aggregate.csv",     index=False)
    tests.to_csv    (out / "statistical_tests.csv",           index=False)
    print(f"[info] wrote aggregated CSVs to {out}")

    # ---- Plots ----
    plot_curve(fit_curve, "best_fitness_mean",   "Best fitness",
               str(plots_dir / "best_fitness_{subject}.png"), "best_fitness_ci95")
    plot_curve(fit_curve, "mean_fitness_mean",   "Mean fitness",
               str(plots_dir / "mean_fitness_{subject}.png"))
    plot_curve(fit_curve, "median_fitness_mean", "Median fitness",
               str(plots_dir / "median_fitness_{subject}.png"))
    plot_curve(fit_curve, "std_fitness_mean",    "Std of fitness",
               str(plots_dir / "std_fitness_{subject}.png"))
    plot_curve(vc_curve,  "valid_count_mean",    "Valid solutions count",
               str(plots_dir / "valid_count_{subject}.png"), "valid_count_std")
    plot_boxplot(summary, "valid_percentage",
                 "Final valid % per run",
                 str(plots_dir / "valid_percentage_boxplot.png"))
    plot_boxplot(summary, "grammar_coverage_score",
                 "Final grammar coverage per run",
                 str(plots_dir / "grammar_coverage_boxplot.png"))
    print(f"[info] wrote plots to {plots_dir}")

    plot_combined_fitness(fit_curve,
                          str(plots_dir / "combined_fitness.png"))


    # ---- Console preview ----
    print("\n=== Valid % (mean ± std) ===")
    print(valid_agg[["condition", "subject", "n_runs", "mean", "std", "median"]]
          .to_string(index=False))
    print("\n=== Grammar coverage (mean ± std) ===")
    print(cov_agg[["condition", "subject", "n_runs", "mean", "std", "median"]]
          .to_string(index=False))
    print("\n=== Efficiency (valid/sec, valid/input) ===")
    print(eff_agg.to_string(index=False))
    if not tests.empty:
        print("\n=== Mann-Whitney U tests ===")
        print(tests.to_string(index=False))



if __name__ == "__main__":
    main()