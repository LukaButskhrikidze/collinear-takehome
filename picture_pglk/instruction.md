# What kind of protein is this?

The picture `/app/data/items/item01.png` shows several experimental structures of
one protein complex made of two identical chains, superposed (cartoon representation,
one colour per structure). The protein's name is withheld.

Answer from the picture and your own knowledge of protein structure and biology.
Do not use the internet or look anything up; the container has no internet access.

## Questions

Answer Q1, Q2, Q4 and Q5 in a few words (1–4), no sentences.

**Q1.** Where in the cell does this protein live?

**Q2.** What class of protein is it?

**Q3.** How many helices cross the membrane in one chain? A whole number (0 if it is
not a membrane protein; do not count re-entrant pore loops).

**Q4.** What powers it?

**Q5.** What molecule does it carry across the membrane?

## Worked example

`/app/data/examples/example.png` is one chain of human KCNQ1 (Kv7.1, UniProt P51787).
Answers that score full marks:

```json
{"Q1": "plasma membrane", "Q2": "voltage-gated potassium channel", "Q3": 6,
 "Q4": "passive, K+ electrochemical gradient", "Q5": "potassium ions"}
```

## Scoring

`/app/data/metric.py` is the exact scoring function. Answers are checked against
UniProt by plain string matching (no AI grader): Q1, Q2, Q4 and Q5 must contain an
accepted term and no contradicting one; Q3 must be the exact number. The five scores
are averaged.

## Answer

Write `/app/answers.json`:

```json
{"item01": {"Q1": "...", "Q2": "...", "Q3": 0, "Q4": "...", "Q5": "..."}}
```
