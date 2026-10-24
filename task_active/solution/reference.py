"""Reference solution: per protein, the experimental monomer ensemble's size and shared core.

Uses only the files in the protein folder (uniprot.fasta + structures/*.cif.gz) and
the container's packages (gemmi, numpy). No SIFTS, no network.

Biology decisions (left free in the task):
- protein atoms only: amino acids incl. modified ones (MSE -> M); ligands, ions,
  water, sugars, nucleic acids, unknown residues (UNK) dropped;
- a residue belongs to the protein only if it aligns to the UniProt sequence:
  expression tags, linkers and fusion partners (T4 lysozyme, BRIL, ...) are dropped,
  residues are numbered by UniProt position, interior point mutations are kept;
- chains of other proteins (partners, homologs) are not this protein.

Pinned conventions (stated in the instruction): first model; first-listed altloc;
copies = first-fit on UniProt overlap > 10 residues; keep members with >= 80% of
the longest member's mapped length; reference = shortest kept; Kabsch on shared
CA with 2 A outlier rejection (5 cycles), 8 A fallback, < 3 inliers = unaligned;
core = UniProt positions present in every aligned member.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import gemmi
import numpy as np

JUNCTION_SLOP = 10
MIN_FRACTION = 0.8
CUTOFF, ACCEPT, CYCLES = 2.0, 8.0, 5
MIN_BLOCK = 8          # aligned blocks shorter than this are chance matches
MIN_IDENTITY = 0.90    # below this the chain is a different protein (homolog/partner)
NUCLEIC = {gemmi.PolymerType.Dna, gemmi.PolymerType.Rna,
           gemmi.PolymerType.DnaRnaHybrid, gemmi.PolymerType.Pna}


# ---------- sequence handling ----------

def read_fasta(path: Path) -> str:
    return "".join(l.strip() for l in path.read_text().splitlines() if not l.startswith(">"))


def letter(name: str) -> str:
    info = gemmi.find_tabulated_residue(name.split(",")[0].strip())
    if info is None or not info.is_amino_acid():
        return "X"
    code = (info.one_letter_code or "").strip().upper()
    return code if code and code not in ".?" else "X"


def is_protein_residue(res: gemmi.Residue) -> bool:
    info = gemmi.find_tabulated_residue(res.name.strip())
    if info is not None and info.is_nucleic_acid():
        return False
    if info is not None and info.is_amino_acid():
        return True
    if res.entity_type in (gemmi.EntityType.NonPolymer, gemmi.EntityType.Water,
                           gemmi.EntityType.Branched, gemmi.EntityType.Polymer):
        return False
    return res.het_flag != "H"


def map_entity(letters: str, uniprot: str) -> dict[int, int]:
    """Entity index (0-based) -> UniProt index (0-based), or {} if not this protein."""
    if len(letters) < MIN_BLOCK:
        return {}
    res = gemmi.align_string_sequences(list(letters), list(uniprot), [],
                                       gemmi.AlignmentScoring("b"))
    blocks, qi, ti = [], 0, 0
    for n, op in _cigar(res.cigar_str()):
        if op == "M":
            blocks.append([(qi + k, ti + k) for k in range(n)])
            qi += n
            ti += n
        elif op == "I":
            qi += n
        else:  # D
            ti += n
    kept = []
    for block in blocks:
        # trim mismatches at block edges (tag/linker residues sliding onto the protein)
        while block and letters[block[0][0]] != uniprot[block[0][1]]:
            block.pop(0)
        while block and letters[block[-1][0]] != uniprot[block[-1][1]]:
            block.pop()
        if len(block) >= MIN_BLOCK:
            kept.append(block)
    mapping = {q: t for block in kept for q, t in block}
    used_t = set(mapping.values())
    # extend blocks over identical neighbours the aligner left out
    # (e.g. a tag that starts with Met stealing UniProt Met1 from the real Met1)
    for block in kept:
        q, t = block[0]
        while q > 0 and t > 0 and q - 1 not in mapping and t - 1 not in used_t \
                and letters[q - 1] == uniprot[t - 1]:
            q, t = q - 1, t - 1
            mapping[q] = t
            used_t.add(t)
        q, t = block[-1]
        while q + 1 < len(letters) and t + 1 < len(uniprot) and q + 1 not in mapping \
                and t + 1 not in used_t and letters[q + 1] == uniprot[t + 1]:
            q, t = q + 1, t + 1
            mapping[q] = t
            used_t.add(t)
    aligned = len(mapping)
    identical = sum(letters[q] == uniprot[t] for q, t in mapping.items())
    if aligned < MIN_BLOCK or identical / aligned < MIN_IDENTITY:
        return {}
    return mapping


def _cigar(cigar: str):
    num = ""
    for ch in cigar:
        if ch.isdigit():
            num += ch
        else:
            yield int(num), ch
            num = ""


# ---------- structures -> members ----------

def entry_members(cif: Path, uniprot: str) -> list[dict[int, np.ndarray]]:
    st = gemmi.read_structure(str(cif))
    st.setup_entities()
    entity_maps = {}
    for ent in st.entities:
        if ent.entity_type != gemmi.EntityType.Polymer or ent.polymer_type in NUCLEIC:
            continue
        letters = "".join(letter(n) for n in ent.full_sequence)
        entity_maps[ent.name] = (letters, map_entity(letters, uniprot))
    model = st[0]
    segments = []  # (sp_beg, sp_end, chain, {uniprot_pos: xyz})
    for chain in model:
        coords: dict[int, np.ndarray] = {}
        for res in chain:
            if not is_protein_residue(res) or res.entity_id not in entity_maps:
                continue
            letters, mapping = entity_maps[res.entity_id]
            idx = res.label_seq - 1 if res.label_seq else None
            if idx is None or idx not in mapping or letters[idx] == "X":
                continue
            pos = mapping[idx] + 1
            ca = next((a for a in res if a.name.strip() == "CA"), None)  # first-listed altloc
            if ca is not None and pos not in coords:
                coords[pos] = np.array(ca.pos.tolist())
        if coords:
            segments.extend(_split_segments(chain.name, coords))
    return [c for c in _color_copies(segments) if c]


def _split_segments(chain: str, coords: dict[int, np.ndarray]):
    """One segment per chain (its UniProt range) — like a SIFTS segment."""
    keys = sorted(coords)
    return [(keys[0], keys[-1], chain, coords)]


def _color_copies(segments):
    ordered = sorted(segments, key=lambda s: (s[0], s[1], s[2]))
    copies: list[list] = []
    for seg in ordered:
        for copy in copies:
            if all(min(seg[1], o[1]) - max(seg[0], o[0]) + 1 <= JUNCTION_SLOP for o in copy):
                copy.append(seg)
                break
        else:
            copies.append([seg])
    merged = []
    for copy in copies:
        coords: dict[int, np.ndarray] = {}
        for seg in sorted(copy, key=lambda s: s[2]):
            for pos, xyz in seg[3].items():
                coords.setdefault(pos, xyz)  # first occurrence wins
        merged.append(coords)
    return merged


# ---------- superposition ----------

def kabsch(p: np.ndarray, q: np.ndarray):
    pm, qm = p.mean(0), q.mean(0)
    u, _s, vt = np.linalg.svd((p - pm).T @ (q - qm))
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[-1] *= -1
        r = vt.T @ u.T
    return r, qm - r @ pm


def _align_at(p: np.ndarray, q: np.ndarray, cutoff: float) -> bool:
    keep = np.ones(len(p), bool)
    r, t = kabsch(p, q)
    for _ in range(CYCLES):
        dist = np.linalg.norm(p @ r.T + t - q, axis=1)
        new_keep = dist <= cutoff
        if new_keep.sum() < 3:
            if keep.sum() <= 3:
                return False
            keep[int(np.argmax(np.where(keep, dist, -np.inf)))] = False
            r, t = kabsch(p[keep], q[keep])
            continue
        if np.array_equal(new_keep, keep):
            break
        keep = new_keep
        r, t = kabsch(p[keep], q[keep])
    return (np.linalg.norm(p @ r.T + t - q, axis=1) <= cutoff).sum() >= 3


def aligns(member: dict, ref: dict) -> bool:
    shared = sorted(set(member) & set(ref))
    if len(shared) < 3:
        return False
    p = np.array([member[k] for k in shared])
    q = np.array([ref[k] for k in shared])
    return _align_at(p, q, CUTOFF) or _align_at(p, q, ACCEPT)


# ---------- per protein ----------

def analyse(folder: Path) -> dict:
    uniprot = read_fasta(folder / "uniprot.fasta")
    members, entries = [], 0
    for cif in sorted((folder / "structures").glob("*.cif*")):
        found = entry_members(cif, uniprot)
        entries += bool(found)
        members.extend(found)
    if not members:
        return {"n_members": 0, "n_core": 0, "n_entries": 0, "n_copies": 0, "n_unaligned": 0}
    longest = max(len(m) for m in members)
    kept = [m for m in members if len(m) >= MIN_FRACTION * longest]
    ref = min(kept, key=len)
    aligned = [m for m in kept if m is ref or aligns(m, ref)]
    core = set.intersection(*(set(m) for m in aligned))
    return {"n_members": len(aligned), "n_core": len(core), "n_entries": entries,
            "n_copies": len(members), "n_unaligned": len(kept) - len(aligned)}


def main(proteins_dir: str, out_csv: str) -> None:
    rows = []
    for folder in sorted(p for p in Path(proteins_dir).iterdir() if p.is_dir()):
        r = analyse(folder)
        rows.append({"protein_id": folder.name, **r})
        print(folder.name, r, flush=True)
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["protein_id", "n_members", "n_core",
                                           "n_entries", "n_copies", "n_unaligned"])
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
