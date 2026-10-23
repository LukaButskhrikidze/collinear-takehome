# Baselines and shortcuts (brief 2.2.6, 2.5)

Each writes an `answers.csv`; score with `tests/score.py`; report reward per subset in `results.json`.

| Script | Rule |
|---|---|
| `null.py` | n_members = number of PDB entries, n_core = UniProt length |
| `naive.py` (cheap tool) | pinned rules on chains as deposited: author numbering, nothing trimmed |
| `../solution/reference.py` | reference (sequence alignment to UniProt with gemmi; no SIFTS) |

Pilot results (provisional truth, 2026-10-23):

| | in_regime | across_boundary | all |
|---|---|---|---|
| null | 0.40 | 0.00 | 0.20 |
| naive | 1.00 | 0.00 | 0.50 |
| reference | 1.00 | 0.96 | 0.98 |

To add: most-common-answer shortcut (median of worked-example-like proteins), and
"number of chains whose sequence matches" (lookup-style count).
