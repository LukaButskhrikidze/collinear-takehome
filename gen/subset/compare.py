"""Per-entry comparison for choosing item subsets (generator side, never shipped).

    python3 compare.py <proteins_dir> <pipeline_copies.json> <out.json> [ACC ...]

For every entry of every protein, three views of the copies (UniProt residue sets):
  pipeline        my pipeline (SIFTS + numbering audit), from gen/subset/pipeline_copies.py
  reference  task/solution/reference.py (sequence alignment to UniProt)
  depositor  the entry's own mapping: _struct_ref_seq rows for this UniProt accession map author residue
             numbers onto UniProt positions; residues outside those rows are dropped (what an agent gets by
             trusting the file's metadata, as Astra did with 5n2r)
An entry is "clean" when pipeline and reference agree copy for copy, and a "trap" when depositor differs from them.
"""
import json
import sys
from pathlib import Path

import gemmi
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "task" / "solution"))
import reference as R  # noqa: E402


def depositor_members(cif: Path, acc: str):
    doc = gemmi.cif.read(str(cif))
    block = doc.sole_block()
    tab = block.find("_struct_ref.", ["id", "pdbx_db_accession"])
    ref_ids = {r[0] for r in tab if gemmi.cif.as_string(r[1]).split("-")[0] == acc} if tab else set()
    rows = []
    srs = block.find("_struct_ref_seq.", ["ref_id", "pdbx_strand_id", "pdbx_auth_seq_align_beg",
                                          "pdbx_auth_seq_align_end", "db_align_beg"])
    for r in srs:
        if r[0] not in ref_ids:
            continue
        try:
            rows.append((gemmi.cif.as_string(r[1]), int(r[2]), int(r[3]), int(r[4])))
        except ValueError:
            continue
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


def counts(members):
    if not members:
        return {"n_members": 0, "n_core": 0}
    longest = max(len(m) for m in members)
    kept = [m for m in members if len(m) >= R.MIN_FRACTION * longest]
    ref = min(kept, key=len)
    aligned = [m for m in kept if m is ref or R.aligns(m, ref)]
    core = set.intersection(*(set(m) for m in aligned))
    return {"n_members": len(aligned), "n_core": len(core)}


def main(proteins_dir, pipeline_json, out_json, *accs):
    pipeline = json.load(open(pipeline_json))
    out = {}
    for acc in accs or sorted(pipeline):
        folder = Path(proteins_dir) / acc
        uni = R.read_fasta(folder / "uniprot.fasta")
        by_pdb = {}
        for c in pipeline[acc]:
            by_pdb.setdefault(c["pdb"].lower(), []).append(sorted(c["res"]))
        entries = []
        for cif in sorted((folder / "structures").glob("*.cif*")):
            pdb = cif.name.split(".")[0].lower()
            ref = sorted(sorted(m) for m in R.entry_members(cif, uni))
            dep = sorted(sorted(m) for m in depositor_members(cif, acc))
            an = sorted(by_pdb.get(pdb, []))
            entries.append({"pdb": pdb, "n_ana": len(an), "n_ref": len(ref), "n_dep": len(dep),
                            "clean": an == ref, "trap": dep != ref,
                            "pipeline": an, "ref": ref, "dep": dep})
        out[acc] = entries
        n_clean = sum(e["clean"] for e in entries)
        n_trap = sum(e["trap"] and e["clean"] for e in entries)
        print(acc, len(entries), "entries;", n_clean, "clean;", n_trap, "clean traps", flush=True)
    json.dump(out, open(out_json, "w"))


if __name__ == "__main__":
    main(*sys.argv[1:])
