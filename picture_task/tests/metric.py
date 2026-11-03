"""Scoring function for the protein-picture task.

Identical copy in tests/metric.py. The verifier uses exactly this; the accepted
terms for each item live with the answer key, not here.

Every text answer is normalised (lower case; anything but letters and digits
becomes a space) and checked with regular expressions:

    Q1, Q2, Q4   text: 1 if an accepted term matches and no rejected term does, else 0
    Q3           whole number: 1 if it equals the key, else 0
    Q5           partners: the first 3 names are kept; each UniProt-listed partner (a gene and its aliases)
                 named counts once; score = min(1, partners named / need), need = 2 (or fewer if UniProt
                 lists fewer)

item reward = mean of the five question scores
task reward = mean over items
subsets     = the questions split in two, each reported as the mean of its questions over all items:
              in_regime       Q1-Q3, read from the picture (location, class, membrane helices)
              across_boundary Q4-Q5, need the protein's family (what activates it, what it binds)
"""
import re

TEXT_QUESTIONS = ("Q1", "Q2", "Q4")
COUNT_QUESTIONS = ("Q3",)
PARTNER_QUESTIONS = ("Q5",)
QUESTIONS = ("Q1", "Q2", "Q3", "Q4", "Q5")
SUBSETS = {"in_regime": ("Q1", "Q2", "Q3"), "across_boundary": ("Q4", "Q5")}
MAX_PARTNERS = 3


def normalise(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(text).lower()).split())


def text_score(answer: str, accept, reject) -> float:
    a = normalise(answer)
    if not a or any(re.search(p, a) for p in reject):
        return 0.0
    return 1.0 if any(re.search(p, a) for p in accept) else 0.0


def count_score(pred: int, truth: int) -> float:
    return 1.0 if pred == truth else 0.0


def partner_score(names, groups, need: int) -> float:
    kept = [normalise(n) for n in names[:MAX_PARTNERS]]
    hit = sum(any(re.search(p, n) for n in kept for p in group) for group in groups)
    return min(1.0, hit / need) if need else 0.0
