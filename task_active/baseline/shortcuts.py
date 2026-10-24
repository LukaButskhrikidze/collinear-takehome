"""Shortcut baselines for the active-state task.

  gprotein : active iff the entry also contains a G protein (alpha subunit / mini-G) or arrestin
  all_active, all_inactive : one label for every entry

    python shortcuts.py <proteins_dir> <out_dir>   -> <out_dir>/{gprotein,all_active,all_inactive}.csv
"""
import csv
import sys
from pathlib import Path

import gemmi

PARTNER = ("subunit alpha", "mini-g", "minig", "mini g", "engineered g", "arrestin")


def has_partner(cif: Path) -> bool:
    desc = " ".join(gemmi.cif.read(str(cif)).sole_block().find_values("_entity.pdbx_description")).lower()
    return any(k in desc for k in PARTNER)


def main(proteins_dir, out_dir):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    rows = {"gprotein": [], "all_active": [], "all_inactive": []}
    for folder in sorted(p for p in Path(proteins_dir).iterdir() if p.is_dir()):
        for cif in sorted((folder / "structures").glob("*.cif*")):
            pdb = cif.name.split(".")[0]
            rows["gprotein"].append((folder.name, pdb, int(has_partner(cif))))
            rows["all_active"].append((folder.name, pdb, 1))
            rows["all_inactive"].append((folder.name, pdb, 0))
    for name, rr in rows.items():
        with open(out / f"{name}.csv", "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["protein_id", "pdb_id", "active"]); w.writerows(rr)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
