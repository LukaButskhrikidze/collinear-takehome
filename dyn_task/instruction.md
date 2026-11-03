# Which protein moves like this?

Each file in `/app/data/items/` (`item01.tsv` … `item12.tsv`) describes how one protein
moves. All experimentally determined structures of the protein were superposed on
their C-alpha atoms, and a principal component analysis (PCA) was run over the
ensemble. The file gives the first principal component (PC1), the largest collective
motion seen across the structures, as a profile along the chain:

- `pct`: position along the resolved core, in 1% steps (`0-1` starts at the first residue
  resolved in every structure, `99-100` ends at the last one; tails resolved in only some
  structures are left out);
- `motion`: average PC1 displacement of the residues in that step, scaled so the largest is 1.00;
- blank `motion`: a gap inside the core, where none of those residues is resolved in every
  structure (often a disordered loop).

The sequence and the protein's name are withheld. Each protein comes with a clue:

| item | clue |
|---|---|
| item01 | a human cytoplasmic enzyme |
| item02 | a human cytoplasmic protein |
| item03 | a cytoplasmic protein from E. coli |
| item04 | a periplasmic protein from E. coli |
| item05 | a periplasmic protein from E. coli |
| item06 | a human cytoplasmic enzyme |
| item07 | a cytoplasmic protein from E. coli |
| item08 | a human cytoplasmic enzyme |
| item09 | a periplasmic protein from E. coli |
| item10 | a periplasmic protein from E. coli |
| item11 | a periplasmic protein from E. coli |
| item12 | a periplasmic protein from E. coli |

Every item is a different protein. Answer from the profiles, the clues and your own
knowledge of protein structure and biology. Do not use the internet or look anything up;
the container has no internet access.

## Questions (for each item)

**Q1.** Which protein is it? Give one gene symbol or protein name.

**Q2.** How many amino acids does its canonical UniProt sequence have? A whole number.

## Worked example

`/app/data/examples/example.tsv` is E. coli adenylate kinase (UniProt P69441), clue "a
cytoplasmic enzyme from E. coli". Its resolved core runs from residue 1 to 213. Its PC1 is
the closing of the AMP-binding (NMP) domain, residues 30–59 (14–27% of the core), and of
the LID domain, residues 122–159 (57–74%), over the rest of the protein. Answers that score
full marks:

```json
{"Q1": "adk", "Q2": 214}
```

## Scoring

`/app/data/metric.py` is the exact scoring function, with no AI grader. Q1 scores 1 if the
answer contains an accepted name of the right protein and no name of another protein (give
one answer, not a list). Q2 scores 1 if it equals the UniProt length exactly. The two scores
are averaged per item, then over items.

## Answer

Write `/app/answers.json`, one entry per item:

```json
{"item01": {"Q1": "...", "Q2": 0},
 "item02": {"Q1": "...", "Q2": 0}}
```
