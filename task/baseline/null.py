"""Null baseline: n_members = number of PDB entries, n_core = UniProt length.

    python null.py <proteins_dir> <answers.csv>
"""
import csv
import sys
from pathlib import Path

rows = []
for folder in sorted(p for p in Path(sys.argv[1]).iterdir() if p.is_dir()):
    seq = "".join(l.strip() for l in (folder / "uniprot.fasta").read_text().splitlines()
                  if not l.startswith(">"))
    rows.append({"protein_id": folder.name,
                 "n_members": len(list((folder / "structures").glob("*.cif*"))),
                 "n_core": len(seq)})
with open(sys.argv[2], "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["protein_id", "n_members", "n_core"])
    w.writeheader()
    w.writerows(rows)
