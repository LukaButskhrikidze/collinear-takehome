# What kind of protein is this?

Each picture in `/app/data/items/` (`item01.png` … `item09.png`) shows one
experimental structure of one protein chain (cartoon representation; dotted lines
are unresolved stretches). Every picture is a different protein, and their names
are withheld.

Answer from the pictures and your own knowledge of protein structure and biology.
Do not use the internet or look anything up; the container has no internet access.

## Questions (for each picture)

Answer Q1, Q2 and Q4 in a few words (1–4), no sentences.

**Q1.** Where in the cell does this protein live?

**Q2.** What class of protein is it?

**Q3.** How many helices cross the membrane in one chain? A whole number (0 if it is
not a membrane protein; do not count re-entrant pore loops).

**Q4.** What signal activates it?

**Q5.** Name up to 3 proteins it binds (gene or protein names). Only the first 3 count.

## Worked example

`/app/data/examples/example.png` is human KCNQ1 (Kv7.1, UniProt P51787). Answers that
score full marks:

```json
{"Q1": "plasma membrane", "Q2": "voltage-gated potassium channel", "Q3": 6,
 "Q4": "membrane depolarization", "Q5": ["KCNE1", "calmodulin"]}
```

## Scoring

`/app/data/metric.py` is the exact scoring function. Answers are checked against
UniProt by plain string matching (no AI grader): Q1, Q2 and Q4 must contain an
accepted term and no contradicting one; Q3 must be the exact number; Q5 earns half
a point for each partner UniProt lists, up to 1. The five scores are averaged per
picture, then over pictures.

## Answer

Write `/app/answers.json`, one entry per picture:

```json
{"item01": {"Q1": "...", "Q2": "...", "Q3": 0, "Q4": "...", "Q5": ["...", "..."]},
 "item02": {...}}
```
