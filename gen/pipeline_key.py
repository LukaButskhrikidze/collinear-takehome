import json, os, sys
import numpy as np
D = sys.argv[1]
for A in sys.argv[2:]:
    P = f"{D}/products/{A}/monomer/sidecar.json"
    s = json.load(open(P))
    sets, missing = [], 0
    for m in s["models"]:
        tr = set()
        for ch in m["chains"]:
            f = f"{D}/derived/coords/{m['pdb_id']}_{ch}_{A}_1.npz"
            if os.path.exists(f):
                tr |= set(int(x) for x in np.load(f)["uniprot_res"])
            else:
                missing += 1
        sets.append(tr)
    inter = set.intersection(*sets) if sets else set()
    pdbs = {m["pdb_id"] for m in s["models"]} | {u["pdb_id"] for u in (s.get("unaligned") or [])}
    size = sum(os.path.getsize(f"{D}/raw/pdb-mmcif/{p[1:3]}/{p}.cif.gz") for p in pdbs)
    L = len("".join(l.strip() for l in open(f"{D}/raw/uniprot/{A}.fasta") if not l.startswith(">")))
    print(f"{A}\tlen={L}\tentries={len(pdbs)}\tmembers={len(s['models'])}\tunaligned={len(s.get('unaligned') or [])}"
          f"\tcore_sidecar={len(s['core_residues'])}\tcore_traces={len(inter)}\tmissing_npz={missing}"
          f"\tMB={size/1e6:.1f}\tmtime={os.path.getmtime(P):.0f}")
