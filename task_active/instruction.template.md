# Active receptor conformations

Each folder `/app/data/proteins/<protein_id>/` holds one G-protein-coupled receptor: its UniProt
sequence (`uniprot.fasta`) and experimental structures of it (`structures/<pdb_id>.cif.gz`,
PDB snapshot 2026-08-30). Use only these files; the container has no internet access.

{TABLE}

**Question:** for every structure, is the receptor in its **active conformation**, the state
that couples to a G protein, or not (inactive or intermediate)?

## Pinned values

model = 1 first model of each entry
copy_rule = majority of receptor copies in the entry decides its label
classes = 2 active (1) versus not active (0)

## Worked example

Orexin-2 receptor (UniProt O43614): `/app/data/examples/O43614/` holds its 12 structures and the
correct labels in `answer.csv` (4 active, 8 not active).

## Tools

Python 3.9 with gemmi 0.7.5, numpy 2.0.2, scipy 1.13.1, PyYAML 6.0.3.
`/app/data/metric.py` is the exact scoring function.

## Answer

Write `/app/answers.csv` with one row per structure:

```
protein_id,pdb_id,active
P30874,7t10,1
...
```

`active` is 1 or 0. Write the file as soon as you have a first answer and update it as you
refine; only the file present at the end is scored. A missing row counts as a wrong label.
