"""Reference: which PDB entries show the receptor in its active (G-protein-competent) state.

Active = TM6 swung outward from TM3 at the cytoplasmic side: Cα(3.50) to Cα(6.34) distance
>= 9.6 Å. Landmarks come from the UniProt sequence (landmarks.py); every receptor copy in an
entry is mapped to UniProt numbering by sequence alignment (fusions, tags, partners dropped);
an entry is active if most of its receptor copies are.

    python reference_active.py <proteins_dir> <answers.csv>
"""
import csv
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from landmarks import find_landmarks  # noqa: E402

try:
    import reference as R  # noqa: E402  (same folder in the container)
except ImportError:
    sys.path.insert(0, str(HERE.parents[1] / "task" / "solution"))
    import reference as R  # noqa: E402

ACTIVE_MIN = 9.6


def entry_state(cif: Path, uniprot: str, p350: int, p634: int):
    dists = [float(np.linalg.norm(c[p350] - c[p634]))
             for c in R.entry_members(cif, uniprot) if p350 in c and p634 in c]
    if not dists:
        return None, []
    return int(sum(d >= ACTIVE_MIN for d in dists) * 2 > len(dists)), dists


def main(proteins_dir: str, out_csv: str) -> None:
    rows = []
    for folder in sorted(p for p in Path(proteins_dir).iterdir() if p.is_dir()):
        uniprot = R.read_fasta(folder / "uniprot.fasta")
        p350, p634 = find_landmarks(uniprot)
        for cif in sorted((folder / "structures").glob("*.cif*")):
            pdb = cif.name.split(".")[0]
            state, _ = entry_state(cif, uniprot, p350, p634) if p350 and p634 else (None, [])
            rows.append({"protein_id": folder.name, "pdb_id": pdb, "active": 0 if state is None else state})
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["protein_id", "pdb_id", "active"])
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
