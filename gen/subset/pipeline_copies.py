"""On the pipeline host (read-only): my pipeline's per-copy UniProt residue sets for each accession, from its per-chain traces.

    python3 pipeline_copies.py <pipeline data root> ACC [ACC ...] > copies.json
"""
import json, os, sys
import numpy as np

D = sys.argv[1]
out = {}
for A in sys.argv[2:]:
    s = json.load(open(f"{D}/products/{A}/monomer/sidecar.json"))
    rows = []
    for kind, models in (("member", s["models"]), ("unaligned", s.get("unaligned") or [])):
        for m in models:
            res = set()
            for ch in m.get("chains") or [m.get("chain")]:
                f = f"{D}/derived/coords/{m['pdb_id']}_{ch}_{A}_1.npz"
                if os.path.exists(f):
                    res |= set(int(x) for x in np.load(f)["uniprot_res"])
            rows.append({"kind": kind, "pdb": m["pdb_id"], "chains": m.get("chains") or [m.get("chain")],
                         "n": len(res), "res": sorted(res), "reason": m.get("reason")})
    out[A] = rows
json.dump(out, sys.stdout)
