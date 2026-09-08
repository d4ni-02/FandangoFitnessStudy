import csv
import logging
import random
import sys
import time
from typing import Optional

from evaluation.csv.csv_evaluation import evaluate_csv
from evaluation.rest.rest_evaluation import evaluate_rest
from evaluation.scriptsizec.scriptsizec_evaluation import evaluate_scriptsizec
from evaluation.tar.tar_evaluation import evaluate_tar
from evaluation.xml.xml_evaluation import evaluate_xml
from fandango.logger import LOGGER

LOGGER.setLevel(logging.WARNING)  # Default


def save_result_to_csv(output_file: str, seconds: int, result: tuple):
    """Salva una riga nel CSV di riepilogo finale con le metriche calcolate."""
    subject, total, valid, valid_pct, coverage, mean_len, median_len = result
    cov_score, cov_current, cov_total = coverage

    row = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "subject": subject,
        "run_time_seconds": seconds,
        "total_inputs": total,
        "valid_solutions": valid,
        "valid_percentage": round(valid_pct, 2),
        "grammar_coverage_score": round(cov_score, 4),
        "covered_rules": cov_current,
        "total_rules": cov_total,
        "mean_length": round(mean_len, 2),
        "median_length": round(median_len, 2),
    }

    # Verifica se il file esiste già per scrivere l'intestazione solo la prima volta
    file_exists = False
    try:
        with open(output_file, mode="r", encoding="utf-8") as f:
            file_exists = True
    except FileNotFoundError:
        file_exists = False

    with open(output_file, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def better_print_results(
    results: tuple[str, int, int, float, tuple[float, int, int], float, float],
):
    print("================================")
    print(f"{results[0]} Evaluation Results")
    print("================================")
    print(f"Total inputs: {results[1]}")
    print(f"Valid {results[0]} solutions: {results[2]} ({results[3]:.2f}%)")
    print(
        f"Grammar coverage (0 to 1): {results[4][0]:.2f} ({results[4][1]} / {results[4][2]})"
    )
    print(f"Mean length: {results[5]:.2f}")
    print(f"Median length: {results[6]:.2f}")
    print("")
    print("")


def run_evaluation(time_limit: Optional[str] = "3600"):
    seconds = 3600
    random_seed = 1

    if time_limit is not None:
        seconds = int(time_limit)
        print(f"Running evaluation with a time limit of {seconds} seconds.")
    else:
        print("Running evaluation with default settings (1 hour).")

    summary_csv_file = "./csv-tests/evaluation_summary_results.csv"
    random.seed(random_seed)

    evaluations = [
        # ("CSV", evaluate_csv),
        ("TAR", evaluate_tar),
        # ("XML", evaluate_xml),
    ]

    for name, eval_func in evaluations:
        ablation_log_path = f"./csv-tests/ablation_generations_{name.lower()}_{seconds}s.csv"
        try:
            res = eval_func(seconds=seconds, ablation_csv_path=ablation_log_path)
            better_print_results(res)
            save_result_to_csv(summary_csv_file, seconds, res)
        except Exception as e:
            print(f"Error in {name}: {e}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    run_evaluation(arg)