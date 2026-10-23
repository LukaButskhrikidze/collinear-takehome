"""Build task/tests/truth.csv and gen/data_card.csv from the answer keys and the shortcut outputs.

    python gen/make_truth.py gen/pipeline_keys_pilot.tsv null.csv naive.csv
baseline_error per number = max(error of the best shortcut, floor); see task/tests/metric.py.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "task" / "tests"))
from metric import baseline_error  # noqa: E402

FIELDS = ("n_members", "n_core")


def read(path, delim=","):
    with open(path, newline="") as fh:
        return {r["protein_id"]: r for r in csv.DictReader(fh, delimiter=delim)}


keys = read(sys.argv[1], "\t")
shortcuts = {"null": read(sys.argv[2]), "naive": read(sys.argv[3])}
truth_rows, card_rows = [], []
for pid, k in keys.items():
    t = {"protein_id": pid, "subset": k["subset"]}
    card = {"protein_id": pid, "subset": k["subset"], "note": k.get("note", "")}
    for f in FIELDS:
        truth = int(k[f])
        vals = {name: int(rows[pid][f]) for name, rows in shortcuts.items()}
        t[f] = truth
        t[f"baseline_error_{f}"] = round(baseline_error(truth, vals.values(), f), 3)
        card[f] = truth
        card.update({f"{name}_{f}": v for name, v in vals.items()})
    truth_rows.append(t)
    card_rows.append(card)

with open(ROOT / "task" / "tests" / "truth.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(truth_rows[0]))
    w.writeheader()
    w.writerows(truth_rows)
with open(ROOT / "gen" / "data_card.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(card_rows[0]))
    w.writeheader()
    w.writerows(card_rows)
print(open(ROOT / "task" / "tests" / "truth.csv").read())
