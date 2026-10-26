"""On the pipeline host (read-only): small proteins whose copies use different author-numbering offsets from UniProt.

    python3 offset_scan.py <pipeline data root> > offsets.tsv
For each monomer product with 6-25 entries and UniProt length <= 260: per copy, the most common
(auth_seq_id - uniprot_res) over mapped residues; report proteins where copies disagree.
"""
import collections, csv, json, os, sys

D = sys.argv[1]
print("uniprot\tlength\tentries\tcopies\tn_offsets\tfrac_off_mode\toffsets\tunmapped_frac")
for u in sorted(os.listdir(f"{D}/products")):
    side = f"{D}/products/{u}/monomer/sidecar.json"
    rmap = f"{D}/products/{u}/monomer/residue_map.tsv"
    fa = f"{D}/raw/uniprot/{u}.fasta"
    if not (os.path.exists(side) and os.path.exists(rmap) and os.path.exists(fa)):
        continue
    try:
        s = json.load(open(side))
    except Exception:
        continue
    pdbs = {m["pdb_id"] for m in s["models"]}
    if not 6 <= len(pdbs) <= 25:
        continue
    L = len("".join(l.strip() for l in open(fa) if not l.startswith(">")))
    if L > 260:
        continue
    offs = collections.defaultdict(collections.Counter)
    unm = tot = 0
    with open(rmap) as fh:
        rows = (l for l in fh if not l.startswith("#"))
        for r in csv.DictReader(rows, delimiter="\t"):
            tot += 1
            if r["status"] != "mapped":
                unm += 1
                continue
            try:
                offs[r["model_id"]][int(r["auth_seq_id"]) - int(r["uniprot_res"])] += 1
            except (ValueError, TypeError):
                pass
    mode_per_copy = [c.most_common(1)[0][0] for c in offs.values() if c]
    if not mode_per_copy:
        continue
    cnt = collections.Counter(mode_per_copy)
    top = cnt.most_common(1)[0][1]
    print(f"{u}\t{L}\t{len(pdbs)}\t{len(mode_per_copy)}\t{len(cnt)}\t{1 - top / len(mode_per_copy):.2f}\t"
          f"{dict(cnt.most_common(4))}\t{unm / max(tot, 1):.3f}", flush=True)
