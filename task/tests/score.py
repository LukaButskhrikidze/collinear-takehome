"""python score.py <answer file> [--truth truth.csv] [--out dir]

Writes reward.txt (float in [0, 1]) and metrics.json. Deterministic, reads only
files on disk, no LLM. A missing or malformed file scores 0 with the reason; a
missing or malformed row scores 0 for that protein and stays in the denominator.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metric import WEIGHTS, number_reward  # noqa: E402

FIELDS = ("n_members", "n_core")


def load_truth(path):
    with open(path, newline="") as fh:
        return {r["protein_id"]: r for r in csv.DictReader(fh)}


def load_answers(path):
    """Return ({protein_id: row or None if duplicated}, file-level error or None)."""
    if not Path(path).is_file():
        return {}, f"answer file not found: {path}"
    try:
        with open(path, newline="") as fh:
            reader = csv.DictReader(fh)
            header = {f.strip() for f in (reader.fieldnames or []) if f}
            if not {"protein_id", *FIELDS} <= header:
                return {}, "header must contain protein_id,n_members,n_core"
            answers = {}
            for row in reader:
                row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
                pid = row.get("protein_id", "")
                answers[pid] = None if pid in answers else row
            return answers, None
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        return {}, f"unreadable answer file: {exc}"


def parse_count(raw):
    """Whole, non-negative number; '24' and '24.0' are both fine, '24.5' is not."""
    value = float(raw)
    if value < 0 or not value.is_integer():
        raise ValueError
    return int(value)


def score(answer_path, truth_path):
    truth = load_truth(truth_path)
    answers, file_error = load_answers(answer_path)
    items = []
    for pid, t in truth.items():
        item = {"protein_id": pid, "subset": t["subset"], "reward": 0.0, "reason": None}
        row = answers.get(pid)
        if file_error:
            item["reason"] = file_error
        elif pid not in answers:
            item["reason"] = "missing row"
        elif row is None:
            item["reason"] = "duplicate rows"
        else:
            total, problems = 0.0, []
            for f in FIELDS:
                truth_v, base = int(t[f]), float(t[f"baseline_error_{f}"])
                item[f"truth_{f}"], item[f"baseline_error_{f}"] = truth_v, base
                try:
                    pred = parse_count(row.get(f, ""))
                    item[f"pred_{f}"] = pred
                    item[f"score_{f}"] = number_reward(pred, truth_v, base)
                except ValueError:
                    item[f"pred_{f}"], item[f"score_{f}"] = None, 0.0
                    problems.append(f"{f} not a whole number: {row.get(f)!r}")
                total += WEIGHTS[f] * item[f"score_{f}"]
            item["reward"] = total
            item["reason"] = "; ".join(problems) or None
        items.append(item)

    def mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    subsets = sorted({i["subset"] for i in items})
    return {
        "reward": mean([i["reward"] for i in items]),
        "per_subset": {s: mean([i["reward"] for i in items if i["subset"] == s]) for s in subsets},
        "n_items": len(items),
        "n_rows_scored_cleanly": sum(i["reason"] is None for i in items),
        "file_error": file_error,
        "items": items,
    }


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("answer")
    ap.add_argument("--truth", default=str(here / "truth.csv"))
    ap.add_argument("--out", default=".")
    args = ap.parse_args()
    metrics = score(args.answer, args.truth)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "reward.txt").write_text(f"{metrics['reward']:.6f}\n")
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps({k: metrics[k] for k in ("reward", "per_subset", "file_error")}))


if __name__ == "__main__":
    main()
