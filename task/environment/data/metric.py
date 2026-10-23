"""Scoring function for the experimental-ensemble task.

Identical copy in tests/metric.py. The verifier uses exactly this.

Each protein has two numbers, n_members and n_core. Each scores

    clip(1 - |pred - truth| / baseline_error, 0, 1)

baseline_error is fixed per protein before any model run: the error of the best
cheap method (counting files / UniProt length, or the pinned rules on chains as
deposited), floored at 1 for n_members and at max(1, 5% of truth) for n_core so
a one-residue numbering judgement costs little. Matching the best cheap method
scores 0; the exact answer scores 1.

protein reward = 0.25 * n_members score + 0.75 * n_core score
task reward    = mean over proteins (also reported per subset)
"""

WEIGHTS = {"n_members": 0.25, "n_core": 0.75}


def number_reward(pred: float, truth: float, baseline_error: float) -> float:
    return min(max(1.0 - abs(pred - truth) / baseline_error, 0.0), 1.0)


def baseline_error(truth: float, shortcut_values, field: str) -> float:
    best = min(abs(v - truth) for v in shortcut_values)
    floor = max(1.0, 0.05 * truth) if field == "n_core" else 1.0
    return max(best, floor)
