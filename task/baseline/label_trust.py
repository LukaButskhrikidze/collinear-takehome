"""Shortcut: trust the file's own UniProt labels (what both smoke-run models did).

For each entry, if _struct_ref_seq labels any segment with the target UniProt accession,
keep only residues inside those segments and number them by the label
(UniProt = db_align_beg + label_seq - seq_align_beg), ignoring positions outside the
UniProt sequence. If the entry has no label for the
target at all, fall back to sequence alignment (the reference's mapping). Then the same
pinned rules: copies, 80% filter, superposition, core.

    python label_trust.py <proteins_dir> <answers.csv>
"""
import csv
import sys
from pathlib import Path

import gemmi
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solution"))
import reference as R  # noqa: E402


def rows(block, name):
    c = block.get_mmcif_category(name)
    keys = list(c)
    n = len(c[keys[0]]) if keys else 0
    return [{k: c[k][i] for k in keys} for i in range(n)]


def target_segments(cif: Path, acc: str):
    """{auth chain: [(seq_beg, seq_end, db_beg)]} for segments labelled with acc."""
    block = gemmi.cif.read(str(cif)).sole_block()
    refs = {r["id"]: r for r in rows(block, "_struct_ref.")}
    out = {}
    for r in rows(block, "_struct_ref_seq."):
        ref = refs.get(r.get("ref_id"), {})
        label = r.get("pdbx_db_accession") or ref.get("pdbx_db_accession")
        if label != acc:
            continue
        try:
            seg = (int(r["seq_align_beg"]), int(r["seq_align_end"]), int(r["db_align_beg"]))
        except (TypeError, ValueError, KeyError):
            continue
        out.setdefault(r["pdbx_strand_id"], []).append(seg)
    return out


def entry_members_labels(cif: Path, uniprot: str, acc: str):
    segs = target_segments(cif, acc)
    if not segs:
        return R.entry_members(cif, uniprot)          # no label for the target: align instead
    st = gemmi.read_structure(str(cif))
    st.setup_entities()
    segments = []
    for chain in st[0]:
        coords = {}
        for res in chain:
            if not R.is_protein_residue(res) or not res.label_seq:
                continue
            for beg, end, db_beg in segs.get(chain.name, []):
                if beg <= res.label_seq <= end:
                    pos = db_beg + res.label_seq - beg
                    if not 1 <= pos <= len(uniprot):      # label points outside the protein: ignore
                        continue
                    ca = next((a for a in res if a.name.strip() == "CA"), None)
                    if ca is not None and pos not in coords:
                        coords[pos] = np.array(ca.pos.tolist())
                    break
        if coords:
            segments.extend(R._split_segments(chain.name, coords))
    return [c for c in R._color_copies(segments) if c]


def analyse(folder: Path) -> dict:
    uniprot = R.read_fasta(folder / "uniprot.fasta")
    members = [m for cif in sorted((folder / "structures").glob("*.cif*"))
               for m in entry_members_labels(cif, uniprot, folder.name)]
    if not members:
        return {"n_members": 0, "n_core": 0}
    longest = max(len(m) for m in members)
    kept = [m for m in members if len(m) >= R.MIN_FRACTION * longest]
    ref = min(kept, key=len)
    aligned = [m for m in kept if m is ref or R.aligns(m, ref)]
    return {"n_members": len(aligned), "n_core": len(set.intersection(*(set(m) for m in aligned)))}


if __name__ == "__main__":
    out_rows = []
    for folder in sorted(p for p in Path(sys.argv[1]).iterdir() if p.is_dir()):
        r = analyse(folder)
        out_rows.append({"protein_id": folder.name, **r})
        print(folder.name, r, flush=True)
    with open(sys.argv[2], "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["protein_id", "n_members", "n_core"])
        w.writeheader()
        w.writerows(out_rows)
