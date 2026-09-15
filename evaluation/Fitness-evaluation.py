import random
import sys
import time
import logging
import csv
from typing import Optional
import multiprocessing

from evaluation.csv.csv_evaluation import evaluate_csv
from evaluation.rest.rest_evaluation import evaluate_rest
from evaluation.scriptsizec.scriptsizec_evaluation import evaluate_scriptsizec
from evaluation.tar.tar_evaluation import evaluate_tar
from evaluation.xml.xml_evaluation import evaluate_xml

from evaluation.byte_evaluation import evaluate_byte
from evaluation.math_evaluation import evaluate_math
from evaluation.person_evaluation import evaluate_person
from fandango.logger import LOGGER

from fandango.language.parse.cache import clear_cache

LOGGER.setLevel(logging.WARNING)  # Default


def save_summary_result_to_csv(output_file: str, seconds: int, result: tuple):
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


def _execute_evaluation_process(eval_func, seconds, ablation_csv_path, queue, seed):
    """Isolate evaluations to avoid cached results"""
    try:
        clear_cache()
        random.seed(seed)
        res = eval_func(seconds=seconds, ablation_csv_path=ablation_csv_path)
        queue.put(("SUCCESS", res))
    except Exception as e:
        queue.put(("ERROR", str(e)))


def run_evaluation(time_limit: Optional[str] = "3600", num_runs: int = 10):
    seconds = 3600
    # random_seed = 1

    if time_limit is not None:
        seconds = int(time_limit)
        print(f"Running evaluation with a time limit of {seconds} seconds.")
    else:
        print("Running evaluation with default settings (1 hour).")

    # random.seed(random_seed)

    evaluations = [
        ("Person", evaluate_person),
        ("Math", evaluate_math),
        ("Byte", evaluate_byte),
    ]

    base_seed = 42
    for run_id in range(1, num_runs + 1):
        print(f"\n{'='*40}")
        print(f"STARTING RUN {run_id} / {num_runs}")
        print(f"{'='*40}")

        # Summary file
        summary_csv_file = f"../csv-tests-alpha015/evaluation_summary_results_run{run_id}.csv"

        run_seed = base_seed + run_id
        
        for name, eval_func in evaluations:
            # ablation results file
            ablation_log_path = f"../csv-tests-alpha015/ablation_generations_{name.lower()}_{seconds}s_run{run_id}.csv"
            
            try:
                print(f"--> Executing {name} (Run {run_id}) on dedicated process...")
                
                queue = multiprocessing.Queue()
                p = multiprocessing.Process(
                    target=_execute_evaluation_process,
                    args=(eval_func, seconds, ablation_log_path, queue, run_seed)
                )
                p.start()
                
                status, data = queue.get()
                p.join()

                if status == "SUCCESS":
                    res = data
                    better_print_results(res)
                    save_summary_result_to_csv(summary_csv_file, seconds, res)
                else:
                    print(f"Error in {name} (Run {run_id}): {data}")

            except Exception as e:
                print(f"Error spawning process for {name} (Run {run_id}): {e}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    run_evaluation(arg)