import argparse
import glob
import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

def compute_ci95(series: pd.Series) -> float:
    n = len(series.dropna())
    if n < 2:
        return 0.0
    sem = stats.sem(series, nan_policy='omit')
    return sem * stats.t.ppf((1 + 0.95) / 2., n - 1)

def process_summaries(input_dir: str) -> pd.DataFrame:
    pattern = os.path.join(input_dir, "evaluation_summary_results_run*.csv")
    files = glob.glob(pattern)
    
    if not files:
        print(f"No summary found: {input_dir}")
        return pd.DataFrame()

    df_list = []
    for f in files:
        match = re.search(r'run(\d+)\.csv$', f)
        run_id = int(match.group(1)) if match else None
        
        df = pd.read_csv(f)
        df['run'] = run_id
        df_list.append(df)

    combined_df = pd.concat(df_list, ignore_index=True)

    metrics = [
        'valid_percentage', 'grammar_coverage_score', 'covered_rules', 
        'valid_solutions', 'total_inputs', 'mean_length', 'median_length'
    ]
    
    agg_funcs = {}
    for m in metrics:
        if m in combined_df.columns:
            agg_funcs[m] = ['mean', 'std', compute_ci95]

    summary_stats = combined_df.groupby('subject').agg(agg_funcs)
    summary_stats.columns = ['_'.join(col).strip() for col in summary_stats.columns.values]
    return summary_stats.reset_index()

def process_generations(input_dir: str) -> pd.DataFrame:
    pattern = os.path.join(input_dir, "ablation_generations_*_run*.csv")
    files = glob.glob(pattern)

    if not files:
        print(f"File not found: {input_dir}")
        return pd.DataFrame()

    df_list = []
    for f in files:
        filename = os.path.basename(f)
        match = re.search(r'ablation_generations_(.+)_600s_run(\d+)\.csv$', filename)
        if match:
            subject = match.group(1)
            run_id = int(match.group(2))
        else:
            continue
            
        df = pd.read_csv(f)
        df['subject'] = subject
        df['run'] = run_id
        df_list.append(df)

    combined_df = pd.concat(df_list, ignore_index=True)

    gen_metrics = ['valid_solutions_count', 'mean_fitness', 'best_fitness']
    
    agg_funcs = {}
    for m in gen_metrics:
        if m in combined_df.columns:
            agg_funcs[m] = ['mean', compute_ci95]

    gen_stats = combined_df.groupby(['subject', 'generation']).agg(agg_funcs)
    gen_stats.columns = ['_'.join(col).strip() for col in gen_stats.columns.values]
    return gen_stats.reset_index()

def plot_combined_fitness(fit_curve: pd.DataFrame, output_path: str) -> None:
    subjects = sorted(fit_curve["subject"].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, len(subjects)))

    fig, ax = plt.subplots(figsize=(12, 7))

    for color, subj in zip(colors, subjects):
        d = fit_curve[fit_curve.subject == subj].sort_values("generation")
        if d.empty:
            continue

        ax.plot(d.generation, d["mean_fitness_mean"],
                color=color, linestyle="-", linewidth=2,
                label=f"{subj} - mean fitness")

        ax.plot(d.generation, d["best_fitness_mean"],
                color=color, linestyle="--", linewidth=2,
                label=f"{subj} - best fitness")
                
        if "best_fitness_compute_ci95" in d.columns:
            ax.fill_between(d.generation,
                            d["best_fitness_mean"] - d["best_fitness_compute_ci95"],
                            d["best_fitness_mean"] + d["best_fitness_compute_ci95"],
                            color=color, alpha=0.15)

    ax.set_xlabel("Generation")
    ax.set_ylabel("Fitness")
    ax.set_title("Mean and Best Fitness vs Generation")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

def plot_valid_solutions_convergence(gen_curve: pd.DataFrame, output_path: str) -> None:
    subjects = sorted(gen_curve["subject"].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, len(subjects)))

    fig, ax = plt.subplots(figsize=(12, 7))

    for color, subj in zip(colors, subjects):
        d = gen_curve[gen_curve.subject == subj].sort_values("generation")
        if d.empty or "valid_solutions_count_mean" not in d.columns:
            continue

        ax.plot(d.generation, d["valid_solutions_count_mean"],
                color=color, linestyle="-", linewidth=2,
                label=f"{subj} - valid solutions")

        if "valid_solutions_count_compute_ci95" in d.columns:
            ax.fill_between(d.generation,
                            d["valid_solutions_count_mean"] - d["valid_solutions_count_compute_ci95"],
                            d["valid_solutions_count_mean"] + d["valid_solutions_count_compute_ci95"],
                            color=color, alpha=0.15)

    ax.set_xlabel("Generation")
    ax.set_ylabel("Valid Solutions Count (Mean)")
    ax.set_title("Valid Solutions Count vs Generation (95% CI)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

def main():
    parser = argparse.ArgumentParser(description="Process fuzzing ablation study results.")
    parser.add_argument("-i", "--input-dir", required=True, help="Input directory containing CSV files")
    parser.add_argument("-o", "--output-dir", required=True, help="Output directory to save results and plots")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"[*] Analisi file in corso da: {args.input_dir}")
    
    # process simmaries
    summary_df = process_summaries(args.input_dir)
    if not summary_df.empty:
        summary_csv_path = os.path.join(args.output_dir, "aggregated_summary_metrics.csv")
        summary_df.to_csv(summary_csv_path, index=False)
        print(f"[+] Metriche di Summary salvate in: {summary_csv_path}")

    # process generations
    generations_df = process_generations(args.input_dir)
    if not generations_df.empty:
        generations_csv_path = os.path.join(args.output_dir, "aggregated_generation_metrics.csv")
        generations_df.to_csv(generations_csv_path, index=False)
        print(f"[+] Metriche Generazionali salvate in: {generations_csv_path}")

        # Plot gen
        fitness_plot_path = os.path.join(args.output_dir, "combined_fitness.png")
        fit_curve = generations_df.rename(columns={"best_fitness_compute_ci95": "best_fitness_ci95"})
        plot_combined_fitness(fit_curve, fitness_plot_path)
        print(f"[+] Grafico Fitness salvato in: {fitness_plot_path}")

        valid_plot_path = os.path.join(args.output_dir, "valid_solutions_convergence.png")
        plot_valid_solutions_convergence(generations_df, valid_plot_path)
        print(f"Plot with solutions saved in: {valid_plot_path}")

    print("OK")

if __name__ == "__main__":
    main()
