"""Screen candidate proteins for the picture task against UniProt (generator side, never shipped).

    python3 screen_candidates.py <out.json> ACC [ACC ...]

For each accession prints the fields the five questions are keyed on:
  Q1 subcellular locations, Q2 class keywords, Q3 transmembrane count,
  Q4 activation keywords + first sentence of Function, Q5 named partners (Subunit text + IntAct binary pairs).
"""
import json
import re
import sys
import urllib.request

CLASS_KW = {"Ion channel", "Voltage-gated channel", "Ligand-gated ion channel", "G-protein coupled receptor",
            "Transducer", "Receptor", "Kinase", "Transport", "Calmodulin-binding", "Potassium channel",
            "Sodium channel", "Calcium channel", "Chloride channel", "Cyclic nucleotide-gated channel"}


def fetch(acc):
    with urllib.request.urlopen(f"https://rest.uniprot.org/uniprotkb/{acc}.json", timeout=60) as r:
        return json.load(r)


def summarise(acc):
    d = fetch(acc)
    out = {"acc": acc, "gene": (d.get("genes") or [{}])[0].get("geneName", {}).get("value"),
           "name": d["proteinDescription"].get("recommendedName", {}).get("fullName", {}).get("value"),
           "organism": d["organism"]["scientificName"], "length": d["sequence"]["length"]}
    out["n_tm"] = sum(f["type"] == "Transmembrane" for f in d.get("features", []))
    out["n_intramembrane"] = sum(f["type"] == "Intramembrane" for f in d.get("features", []))
    locs, function, subunit = [], "", ""
    for c in d.get("comments", []):
        if c["commentType"] == "SUBCELLULAR LOCATION":
            locs += [l["location"]["value"] + ("/" + l["topology"]["value"] if "topology" in l else "")
                     for l in c.get("subcellularLocations", [])]
        elif c["commentType"] == "FUNCTION" and not function:
            function = " ".join(t["value"] for t in c.get("texts", []))
        elif c["commentType"] == "SUBUNIT":
            subunit += " ".join(t["value"] for t in c.get("texts", []))
    out["locations"] = locs
    out["keywords"] = sorted(k["name"] for k in d.get("keywords", []) if k["name"] in CLASS_KW
                             or k["category"] in ("Molecular function",))
    out["function_start"] = re.sub(r"\s*\(PubMed:[^)]*\)", "", function)[:300]
    out["subunit_partners"] = sorted(set(re.findall(r"[Ii]nteracts? (?:\([^)]*\) )?with ([A-Z][A-Z0-9]{2,})", subunit)))
    out["subunit_text"] = re.sub(r"\s*\(PubMed:[^)]*\)", "", subunit)[:400]
    out["intact"] = sorted({i.get("interactantTwo", {}).get("geneName") for c in d.get("comments", [])
                            if c["commentType"] == "INTERACTION" for i in c.get("interactions", [])} - {None, out["gene"]})
    return out


def main(out_json, *accs):
    res = []
    for acc in accs:
        try:
            s = summarise(acc)
        except Exception as exc:  # noqa: BLE001
            print(acc, "ERROR", exc)
            continue
        res.append(s)
        print(f"{acc} {s['gene']} | {s['name']} | {s['organism']} | len {s['length']} | TM {s['n_tm']}+{s['n_intramembrane']}i")
        print("   loc:", s["locations"][:4])
        print("   kw:", [k for k in s["keywords"] if k in CLASS_KW])
        print("   fn:", s["function_start"][:200])
        print("   partners:", s["subunit_partners"][:10], "| intact:", s["intact"][:8])
    json.dump(res, open(out_json, "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:])
