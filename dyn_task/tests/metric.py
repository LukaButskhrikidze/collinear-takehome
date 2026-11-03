"""Scoring function for the motion-fingerprint task.

Identical copy in tests/metric.py. The verifier uses exactly this; the accepted and
rejected names for each item live with the answer key, not here.

    Q1   protein name: normalised (lower case; anything but letters and digits becomes a
         space); 1 if an accepted name for that protein matches and no other protein's
         name does, else 0
    Q2   canonical UniProt length: 1 if the whole number equals the key, else 0

item reward = mean of Q1 and Q2
task reward = mean over items
subsets     = items split in two, each reported as the mean item reward:
              in_regime       the clue and the motion point to one protein family
              across_boundary periplasmic binding proteins: one clue and one fold for all, only
                              the hinge layout in the motion profile tells them apart
"""
import re

QUESTIONS = ("Q1", "Q2")


def normalise(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(text).lower()).split())


def name_score(answer: str, accept, reject) -> float:
    a = normalise(answer)
    if not a or any(re.search(p, a) for p in reject):
        return 0.0
    return 1.0 if any(re.search(p, a) for p in accept) else 0.0


def length_score(pred: int, truth: int) -> float:
    return 1.0 if pred == truth else 0.0
