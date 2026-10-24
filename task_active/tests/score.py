"""python score.py <answer file> [--truth truth.csv] [--receptors receptors.csv] [--out dir]

Writes reward.txt (float in [0, 1]) and metrics.json, and keeps a copy of the answer file.
Deterministic, reads only files on disk, no LLM. A missing or malformed file scores 0 with the
reason; a missing, duplicated or unreadable row counts as a wrong label and stays in the
denominator.
"""
import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metric import receptor_reward  # noqa: E402

TRUE = {"1", "true", "active", "yes"}
FALSE = {"0", "false", "inactive", "no"}


def load_answers(path):
    if not Path(path).is_file():
        return {}, f"answer file not found: {path}"
    try:
        with open(path, newline="") as fh:
            reader = csv.DictReader(fh)
            header = {f.strip() for f in (reader.fieldnames or []) if f}
            if not {"protein_id", "pdb_id", "active"} <= header:
                return {}, "header must contain protein_id,pdb_id,active"
            out = {}
            for row in reader:
                row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
                key = (row.get("protein_id", ""), row.get("pdb_id", "").lower())
                raw = row.get("active", "").lower()
                value = 1 if raw in TRUE else 0 if raw in FALSE else None
                out[key] = "duplicate" if key in out else value
            return out, None
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        return {}, f"unreadable answer file: {exc}"


def score(answer_path, truth_path, receptors_path):
    truth = [r for r in csv.DictReader(open(truth_path, newline=""))]
    receptors = {r["protein_id"]: r for r in csv.DictReader(open(receptors_path, newline=""))}
    answers, file_error = load_answers(answer_path)
    per = {}
    for r in truth:
        pid, pdb, lab = r["protein_id"], r["pdb_id"].lower(), int(r["active"])
        item = per.setdefault(pid, {"protein_id": pid, "subset": receptors[pid]["subset"],
                                    "baseline_error": float(receptors[pid]["baseline_error"]),
                                    "n_entries": 0, "errors": 0, "missing": 0, "wrong": []})
        item["n_entries"] += 1
        pred = None if file_error else answers.get((pid, pdb))
        if pred is None or pred == "duplicate":
            item["errors"] += 1
            item["missing"] += 1
        elif pred != lab:
            item["errors"] += 1
            item["wrong"].append(pdb)
    for item in per.values():
        item["reward"] = receptor_reward(item["errors"], item["baseline_error"])

    def mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    items = list(per.values())
    subsets = sorted({i["subset"] for i in items})
    return {
        "reward": mean([i["reward"] for i in items]),
        "per_subset": {s: mean([i["reward"] for i in items if i["subset"] == s]) for s in subsets},
        "file_error": file_error,
        "items": items,
    }


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("answer")
    ap.add_argument("--truth", default=str(here / "truth.csv"))
    ap.add_argument("--receptors", default=str(here / "receptors.csv"))
    ap.add_argument("--out", default=".")
    args = ap.parse_args()
    metrics = score(args.answer, args.truth, args.receptors)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "reward.txt").write_text(f"{metrics['reward']:.6f}\n")
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    if Path(args.answer).is_file():
        shutil.copy(args.answer, out / "answers_submitted.csv")
    print(json.dumps({k: metrics[k] for k in ("reward", "per_subset", "file_error")}))


if __name__ == "__main__":
    main()
