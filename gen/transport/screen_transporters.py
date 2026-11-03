"""Screen membrane transporters for the picture task (generator side, never shipped).

    python3 screen_transporters.py <available_mapping.json> <out.tsv>

1. UniProt (reviewed, Transport + Transmembrane keywords, has 3D structure, not an ion channel), all organisms,
   with TCDB id, keywords, subcellular location, catalytic activity (Rhea) and transmembrane features.
2. Keep proteins my pipeline has, with their number of aligned monomer chains.
3. Derive the answer fields: transport type (TCDB class + keywords), driving force, cargo, location, TM count.
"""
import csv
import io
import json
import re
import sys
import urllib.parse
import urllib.request

FIELDS = ["accession", "gene_primary", "protein_name", "organism_name", "length", "xref_tcdb", "keyword",
          "cc_subcellular_location", "cc_catalytic_activity", "ft_transmem", "ft_intramem", "cc_function"]
QUERY = ("reviewed:true AND keyword:KW-0813 AND keyword:KW-0812 AND structure_3d:true "
         "AND NOT keyword:KW-0407")


def fetch():
    url = ("https://rest.uniprot.org/uniprotkb/stream?format=tsv&fields=" + ",".join(FIELDS)
           + "&query=" + urllib.parse.quote(QUERY))
    with urllib.request.urlopen(url, timeout=600) as r:
        return list(csv.DictReader(io.StringIO(r.read().decode()), delimiter="\t"))


def transport_type(kw, tcdb):
    k = kw.lower()
    if "symport" in k:
        return "symporter"
    if "antiport" in k:
        return "antiporter"
    if tcdb.startswith("3.A.1."):
        return "ABC transporter"
    if tcdb.startswith("3."):
        return "primary active (pump)"
    if tcdb.startswith("2."):
        return "secondary/uniporter"
    if tcdb.startswith("1."):
        return "channel/pore"
    return ""


def driving_force(kw, tcdb, fn):
    k, f = kw.lower(), fn.lower()
    if "atp-binding" in k and tcdb.startswith("3."):
        return "ATP"
    if "sodium transport" in k or "sodium-coupled" in f or "na(+)-coupled" in f or "sodium-dependent" in f:
        return "Na+ gradient"
    if "proton" in f and ("symport" in k or "antiport" in k or "proton-coupled" in f or "h(+)-coupled" in f):
        return "H+ gradient"
    if "uniport" in f or "facilitative" in f or "facilitated" in f:
        return "none (facilitated)"
    return ""


def cargo(cat):
    # substrates from the Rhea equations, ions and water dropped
    subs = set()
    for eq in re.findall(r"Reaction=([^;]+);", cat):
        left = eq.split("=")[0]
        for part in left.split(" + "):
            name = re.sub(r"\((in|out)\)", "", part).strip()
            if name and not re.fullmatch(r"(H\(\+\)|Na\(\+\)|K\(\+\)|Cl\(-\)|H2O|ATP|ADP|phosphate|\d+ .*)", name):
                subs.add(name)
    return sorted(subs)[:6]


def main(mapping_json, out_tsv):
    mapping = json.load(open(mapping_json))
    rows = fetch()
    print("UniProt transporters with structures:", len(rows))
    out = []
    for r in rows:
        acc = r["Entry"]
        if acc not in mapping:
            continue
        n_chains = sum(not k.startswith("oligomers/") for k in mapping[acc])
        tcdb = (r["TCDB"] or "").split(";")[0].strip()
        kw, fn = r["Keywords"] or "", r["Function [CC]"] or ""
        loc = re.sub(r"\{[^}]*\}", "", (r["Subcellular location [CC]"] or "").replace("SUBCELLULAR LOCATION: ", ""))
        out.append({
            "acc": acc, "gene": r["Gene Names (primary)"], "organism": r["Organism"][:40], "length": r["Length"],
            "n_chains": n_chains, "tcdb": tcdb, "tcdb_family": ".".join(tcdb.split(".")[:3]),
            "n_tm": r["Transmembrane"].count("TRANSMEM"), "n_intramem": r["Intramembrane"].count("INTRAMEM"),
            "type": transport_type(kw, tcdb), "force": driving_force(kw, tcdb, fn),
            "cargo": "; ".join(cargo(r["Catalytic activity"] or "")),
            "location": re.sub(r"\s+", " ", loc).strip()[:120], "name": r["Protein names"][:70],
        })
    out.sort(key=lambda x: (x["tcdb_family"], -x["n_chains"]))
    with open(out_tsv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]), delimiter="\t")
        w.writeheader()
        w.writerows(out)
    print("in my pipeline:", len(out), "| with >= 3 chains:", sum(x["n_chains"] >= 3 for x in out))


if __name__ == "__main__":
    main(*sys.argv[1:])
