"""Scoring function for the active-state task. Identical copy in tests/metric.py.

Per receptor:
    errors         = entries whose label is wrong; a missing or unreadable row counts as wrong
    baseline_error = errors of the best label-free shortcut on that receptor (fixed in advance:
                     'active iff a G protein or arrestin is bound', 'all active', 'all inactive'),
                     floored at 1
    reward         = clip(1 - errors / baseline_error, 0, 1)

Matching the best shortcut scores 0; labelling every entry right scores 1. The task reward is
the mean over receptors, also reported per subset.
"""


def receptor_reward(errors: int, baseline_error: float) -> float:
    return min(max(1.0 - errors / max(baseline_error, 1.0), 0.0), 1.0)
