# Experimental conformational ensembles

For each protein below, `/app/data/proteins/<protein_id>/` holds its UniProt
sequence (`uniprot.fasta`) and every PDB entry that contains it
(`structures/<pdb_id>.cif.gz`, snapshot 2026-08-30). Use only these files; the
container has no internet access.

| protein_id | Protein | Organism | PDB entries |
|---|---|---|---|
| O66490 | Adenylate kinase | Aquifex aeolicus | 14 |
| P43408 | Adenylate kinase | Methanotorris igneus | 3 |
| P07550 | Beta-2 adrenergic receptor | Homo sapiens | 130 |
| P29274 | Adenosine receptor A2a | Homo sapiens | 188 |

**Question, for each protein:** build the protein's experimental monomer
ensemble — every copy of the protein found in these entries, superposed onto one
reference — and report

- `n_members`: how many structures (protein copies) the ensemble contains;
- `n_core`: how many UniProt residue positions are present in every member.

Count only residues of the protein named by the UniProt entry, numbered by their
UniProt position.

## Pinned values

model = 1 first model of each entry
altloc = first listed alternate location
copy_overlap = 10 residues of UniProt overlap above which two chain pieces are separate copies
min_fraction = 0.80 fraction of the longest member's residue count needed to stay in the ensemble
fit_cutoff = 2.0 Å outlier cutoff for iterative Cα superposition
fit_cycles = 5 cycles
fit_fallback = 8.0 Å cutoff retried when fewer than 3 Cα pairs survive at fit_cutoff

- A copy is one occurrence of the protein in an entry. Pieces of one copy can sit in
  different chains; two pieces whose UniProt ranges overlap by more than
  `copy_overlap` residues are different copies.
- Count residues that have a Cα atom.
- The reference is the shortest member left after `min_fraction`.
- Superpose each member onto the reference on Cα atoms at shared UniProt positions:
  least-squares fit, then refit on pairs within `fit_cutoff` for up to `fit_cycles`
  cycles; if fewer than 3 pairs survive, retry at `fit_fallback`; a member that still
  has fewer than 3 is not in the ensemble.
- `n_core` counts positions present in every member of the final ensemble.

## Worked example

E. coli adenylate kinase (UniProt P69441), in `/app/data/examples/P69441/`
(29 PDB entries): `n_members = 55`, `n_core = 181`.

## Tools

Python 3.9 with gemmi 0.7.5, numpy 2.0.2, scipy 1.13.1, PyYAML 6.0.3.
`/app/data/metric.py` is the exact scoring function.

## Answer

Write `/app/answers.csv`, one row per protein:

```
protein_id,n_members,n_core
O66490,...,...
```

Both values are whole numbers. Extra columns are ignored.
