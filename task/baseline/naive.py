"""Naive baseline (cheap tool): the pinned rules on chains exactly as deposited.

Chains are picked the same way as the reference (sequence matches the UniProt
protein), but every protein residue is kept and numbered by its author residue
number: no trimming of tags, linkers or fusion partners, no renumbering to UniProt.

    python naive.py <proteins_dir> <answers.csv>
"""
import csv
import sys
from pathlib import Path

import gemmi
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solution"))
import reference as R  # noqa: E402


def entry_members_naive(cif: Path, uniprot: str):
    st = gemmi.read_structure(str(cif))
    st.setup_entities()
    ours = {e.name for e in st.entities
            if e.entity_type == gemmi.EntityType.Polymer and e.polymer_type not in R.NUCLEIC
            and R.map_entity("".join(R.letter(n) for n in e.full_sequence), uniprot)}
    segments = []
    for chain in st[0]:
        coords = {}
        for res in chain:
            if res.entity_id not in ours or not R.is_protein_residue(res):
                continue
            ca = next((a for a in res if a.name.strip() == "CA"), None)
            if ca is not None and res.seqid.num not in coords:
                coords[res.seqid.num] = np.array(ca.pos.tolist())
        if coords:
            segments.extend(R._split_segments(chain.name, coords))
    return [c for c in R._color_copies(segments) if c]


def analyse(folder: Path) -> dict:
    uniprot = R.read_fasta(folder / "uniprot.fasta")
    members = [m for cif in sorted((folder / "structures").glob("*.cif*"))
               for m in entry_members_naive(cif, uniprot)]
    if not members:
        return {"n_members": 0, "n_core": 0}
    longest = max(len(m) for m in members)
    kept = [m for m in members if len(m) >= R.MIN_FRACTION * longest]
    ref = min(kept, key=len)
    aligned = [m for m in kept if m is ref or R.aligns(m, ref)]
    return {"n_members": len(aligned), "n_core": len(set.intersection(*(set(m) for m in aligned)))}


if __name__ == "__main__":
    rows = []
    for folder in sorted(p for p in Path(sys.argv[1]).iterdir() if p.is_dir()):
        r = analyse(folder)
        rows.append({"protein_id": folder.name, **r})
        print(folder.name, r, flush=True)
    with open(sys.argv[2], "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["protein_id", "n_members", "n_core"])
        w.writeheader()
        w.writerows(rows)
