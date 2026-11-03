"""python score.py <answer file> [--truth truth.json] [--out dir]

Writes reward.txt (float in [0, 1]) and metrics.json. Deterministic, reads only
files on disk, no LLM. A missing or malformed file scores 0 with the reason; a
missing item or a malformed answer scores 0 for that item or question and stays
in the denominator.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metric import (COUNT_QUESTIONS, PARTNER_QUESTIONS, QUESTIONS, SUBSETS, TEXT_QUESTIONS,  # noqa: E402
                    count_score, partner_score, text_score)


def load_answers(path):
    """Return ({item_id: answer dict}, file-level error or None)."""
    if not Path(path).is_file():
        return {}, f"answer file not found: {path}"
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {}, f"unreadable answer file: {exc}"
    if not isinstance(data, dict):
        return {}, "answer file must be a JSON object keyed by item id"
    return data, None


def parse_text(raw):
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"not a non-empty string: {raw!r}")
    return raw.strip()


def parse_count(raw):
    """Whole, non-negative number; 6 and 6.0 are both fine, 6.5 is not."""
    value = float(raw)
    if value < 0 or not value.is_integer():
        raise ValueError(f"not a whole number: {raw!r}")
    return int(value)


def parse_names(raw):
    if isinstance(raw, str):
        raw = raw.replace(";", ",").split(",")
    if not isinstance(raw, list):
        raise ValueError(f"not a list of names: {raw!r}")
    names = [str(x).strip() for x in raw if str(x).strip()]
    if not names:
        raise ValueError("no names given")
    return names


def score_question(q, raw, t):
    if q in TEXT_QUESTIONS:
        pred = parse_text(raw)
        return pred, text_score(pred, t["accept"], t["reject"])
    if q in COUNT_QUESTIONS:
        pred = parse_count(raw)
        return pred, count_score(pred, int(t["key"]))
    if q in PARTNER_QUESTIONS:
        pred = parse_names(raw)
        return pred, partner_score(pred, t["groups"], t["need"])
    raise KeyError(q)


def score(answer_path, truth_path):
    truth = json.loads(Path(truth_path).read_text())
    answers, file_error = load_answers(answer_path)
    items = []
    for item_id, t in truth.items():
        item = {"item_id": item_id, "reward": 0.0, "reason": None}
        row = answers.get(item_id)
        if file_error:
            item["reason"] = file_error
        elif not isinstance(row, dict):
            item["reason"] = "missing item" if row is None else "item answer is not an object"
        else:
            problems, scores = [], []
            for q in QUESTIONS:
                item[f"truth_{q}"] = t[q]["key"]
                try:
                    pred, s = score_question(q, row[q], t[q])
                except KeyError:
                    pred, s = None, 0.0
                    problems.append(f"{q}: missing")
                except (TypeError, ValueError) as exc:
                    pred, s = None, 0.0
                    problems.append(f"{q}: {exc}")
                item[f"pred_{q}"], item[f"score_{q}"] = pred, s
                scores.append(s)
            item["reward"] = sum(scores) / len(scores)
            item["reason"] = "; ".join(problems) or None
        items.append(item)

    def mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    per_question = {q: mean([i.get(f"score_{q}", 0.0) for i in items]) for q in QUESTIONS}
    return {
        "reward": mean([i["reward"] for i in items]),
        "per_subset": {name: mean([per_question[q] for q in qs]) for name, qs in SUBSETS.items()},
        "per_question": per_question,
        "n_items": len(items),
        "n_items_scored_cleanly": sum(i["reason"] is None for i in items),
        "file_error": file_error,
        "items": items,
    }


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("answer")
    ap.add_argument("--truth", default=str(here / "truth.json"))
    ap.add_argument("--out", default=".")
    args = ap.parse_args()
    metrics = score(args.answer, args.truth)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "reward.txt").write_text(f"{metrics['reward']:.6f}\n")
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps({k: metrics[k] for k in ("reward", "per_subset", "per_question", "file_error")}))


if __name__ == "__main__":
    main()
