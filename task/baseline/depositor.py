"""Depositor-mapping baseline: trust each entry's own mapping to UniProt.

For every chain, the entry's _struct_ref_seq rows that cite this UniProt accession map author residue
numbers onto UniProt positions; residues outside those rows are dropped. Then the pinned rules, as in
the reference. This is what an agent gets by trusting the file's metadata instead of the sequence.

    python depositor.py <proteins_dir> <answers.csv>
"""
import csv
import sys
from pathlib import Path

import gemmi
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solution"))
import reference as R  # noqa: E402


def entry_members_depositor(cif: Path, acc: str):
    block = gemmi.cif.read(str(cif)).sole_block()
    refs = block.find("_struct_ref.", ["id", "pdbx_db_accession"])
    ids = {r[0] for r in refs if gemmi.cif.as_string(r[1]).split("-")[0] == acc}
    rows = []
    for r in block.find("_struct_ref_seq.", ["ref_id", "pdbx_strand_id", "pdbx_auth_seq_align_beg",
                                             "pdbx_auth_seq_align_end", "db_align_beg"]):
        if r[0] in ids:
            try:
                rows.append((gemmi.cif.as_string(r[1]), int(r[2]), int(r[3]), int(r[4])))
            except ValueError:
                pass
    st = gemmi.read_structure(str(cif))
    segments = []
    for chain in st[0]:
        coords = {}
        for res in chain:
            if not R.is_protein_residue(res):
                continue
            for ch, beg, end, db in rows:
                if ch == chain.name and beg <= res.seqid.num <= end:
                    pos = db + (res.seqid.num - beg)
                    ca = next((a for a in res if a.name.strip() == "CA"), None)
                    if ca is not None and pos not in coords:
                        coords[pos] = np.array(ca.pos.tolist())
                    break
        if coords:
            segments.extend(R._split_segments(chain.name, coords))
    return [c for c in R._color_copies(segments) if c]


def analyse(folder: Path, acc: str) -> dict:
    members = []
    for cif in sorted((folder / "structures").glob("*.cif*")):
        members.extend(entry_members_depositor(cif, acc))
    if not members:
        return {"n_members": 0, "n_core": 0}
    longest = max(len(m) for m in members)
    kept = [m for m in members if len(m) >= R.MIN_FRACTION * longest]
    ref = min(kept, key=len)
    aligned = [m for m in kept if m is ref or R.aligns(m, ref)]
    return {"n_members": len(aligned), "n_core": len(set.intersection(*(set(m) for m in aligned)))}


def main(proteins_dir: str, out_csv: str) -> None:
    rows = [{"protein_id": f.name, **analyse(f, f.name)}
            for f in sorted(p for p in Path(proteins_dir).iterdir() if p.is_dir())]
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["protein_id", "n_members", "n_core"])
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
