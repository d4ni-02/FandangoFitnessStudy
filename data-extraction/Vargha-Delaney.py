import glob
import os
import numpy as np
import pandas as pd
from scipy.stats import rankdata



def interpret_a12(a12):
    """Restituisce l'interpretazione qualitativa dell'effetto A12."""
    if np.isnan(a12):
        return "N/A"
    d = abs(a12 - 0.5)
    if d < 0.06:  # < 0.56
        effect = "Trascurabile"
    elif d < 0.14:  # < 0.64
        effect = "Piccolo"
    elif d < 0.21:  # < 0.71
        effect = "Medio"
    else:  # >= 0.71
        effect = "Grande"

    direction = "Migliore" if a12 > 0.5 else ("Peggiore" if a12 < 0.5 else "Uguale")
    return f"{effect} ({direction})"

def vargha_delaney_a12(treatment, baseline):
    m, n = len(treatment), len(baseline)
    if m == 0 or n == 0:
        return np.nan
    r = rankdata(np.concatenate([treatment, baseline]))
    r1 = sum(r[:m])
    return (r1 / m - (m + 1) / 2) / n


# Dirs
folders = {
    "Linear": "csv-tests-Linear",
    "alpha=0.15": "csv-tests-alpha015",
    "alpha=0.5": "csv-tests-alpha05",
    "alpha=2.0": "csv-tests-alpha2",
}

# column metric ('valid_solutions' or 'valid_percentage')
METRIC = "valid_solutions"

data = {cfg: {} for cfg in folders}

# Read CSV
for cfg_name, folder_path in folders.items():
    csv_files = glob.glob(os.path.join(folder_path, "evaluation_summary_results_*.csv"))

    for filepath in csv_files:
        try:
            df = pd.read_csv(filepath)
            for _, row in df.iterrows():
                # normalize name
                subj = str(row["subject"]).strip().upper()
                val = float(row[METRIC])

                if subj not in data[cfg_name]:
                    data[cfg_name][subj] = []
                data[cfg_name][subj].append(val)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")

baseline_cfg = "Linear"
subjects = sorted(list(data[baseline_cfg].keys()))
results = []

for subj in subjects:
    base_vals = data[baseline_cfg].get(subj, [])

    for cfg_name in folders:
        if cfg_name == baseline_cfg:
            continue

        treat_vals = data[cfg_name].get(subj, [])
        a12_score = vargha_delaney_a12(treat_vals, base_vals)

        results.append({
            "Subject": subj,
            "Config vs Baseline": f"{cfg_name} vs Linear",
            "Mean (Alpha)": round(np.mean(treat_vals), 2) if treat_vals else 0,
            "Mean (Linear)": round(np.mean(base_vals), 2) if base_vals else 0,
            "A12 Score": round(a12_score, 4),
            "Effetto A12": interpret_a12(a12_score),
        })

# Stampa i risultati
df_res = pd.DataFrame(results)
print(f"\n================ A12 on matric: {METRIC} ================\n")
print(df_res.to_string(index=False))