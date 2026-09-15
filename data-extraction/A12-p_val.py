#!/usr/bin/env python3
"""
Confronta valid_percentage tra ogni alpha e Linear.
Calcola Mann-Whitney U (p-value) e A12 Vargha-Delaney.
"""

import os
import glob
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

BASE = "."
LINEAR_DIR = os.path.join(BASE, "csv-tests-Linear")
ALPHA_DIRS = {
    "alpha015": os.path.join(BASE, "csv-tests-alpha015"),
    "alpha05":  os.path.join(BASE, "csv-tests-alpha05"),
    "alpha2":   os.path.join(BASE, "csv-tests-alpha2"),
}


def load_summaries(directory):
    """Carica e concatena tutti gli evaluation_summary_results_run*.csv di una dir."""
    files = sorted(glob.glob(os.path.join(directory, "evaluation_summary_results_run*.csv")))
    if not files:
        raise FileNotFoundError(f"Nessun summary trovato in {directory}")
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def vargha_delaney_a12(x, y):
    """
    A12 = P(X > Y) + 0.5 * P(X == Y), stimato sulle osservazioni.
    A12 > 0.5 -> X tende a essere maggiore di Y
    A12 = 0.5 -> nessuna differenza stocastica
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) == 0 or len(y) == 0:
        return np.nan
    gt = (x[:, None] > y[None, :]).sum()
    eq = (x[:, None] == y[None, :]).sum()
    return (gt + 0.5 * eq) / (len(x) * len(y))


def main():
    linear_df = load_summaries(LINEAR_DIR)
    subjects = sorted(linear_df["subject"].dropna().unique())

    rows = []
    for alpha_name, alpha_dir in ALPHA_DIRS.items():
        alpha_df = load_summaries(alpha_dir)
        for subj in subjects:
            x = alpha_df.loc[alpha_df["subject"] == subj, "valid_percentage"].dropna().values
            y = linear_df.loc[linear_df["subject"] == subj, "valid_percentage"].dropna().values
            if len(x) == 0 or len(y) == 0:
                continue

            u_stat, p = mannwhitneyu(x, y, alternative="two-sided")
            a12 = vargha_delaney_a12(x, y)

            rows.append({
                "alpha": alpha_name,
                "subject": subj,
                # "n_alpha": len(x),
                # "n_linear": len(y),
                # "mean_alpha": np.mean(x),
                # "mean_linear": np.mean(y),
                # "median_alpha": np.median(x),
                # "median_linear": np.median(y),
                # "U": u_stat,
                "p_value": p,
                "A12": a12,
                # lettura rapida del verso dell'effetto
                "direction": ("alpha>linear" if a12 > 0.5 else
                              "alpha<linear" if a12 < 0.5 else "="),
            })

    res = pd.DataFrame(rows).sort_values(["subject", "alpha"]).reset_index(drop=True)

    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.float_format", lambda v: f"{v:.4f}")
    print(res.to_string(index=False))

    out = "mannwhitney_a12_valid_percentage.csv"
    res.to_csv(out, index=False)
    print(f"\nSalvato: {out}")


if __name__ == "__main__":
    main()