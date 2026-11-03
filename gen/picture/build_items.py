"""Build the picture-task items, answer key and placeholder oracle answers (generator side, never shipped).

    <python with Pillow> build_items.py

Inputs : gen/picture/screens/<GENE>.png   one screenshot per protein (single structure, single angle)
Outputs: picture_task/environment/data/items/itemNN.png   cropped, metadata-free, shuffled (seed 7)
         picture_task/environment/data/examples/example.png   KCNQ1, the worked example
         picture_task/tests/truth.json   accepted / rejected terms per question, from UniProt (2026-10-28)
         picture_task/solution/answers.json   answers that the key accepts (placeholder oracle)
         gen/picture/item_map.json   itemNN -> protein (local only)
"""
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SCREENS = ROOT / "gen/picture/screens"
DATA = ROOT / "picture_task/environment/data"
SEED = 7

# ---- Q1 location -------------------------------------------------------------------------------
PM = {"accept": [r"\bmembrane\b", r"\btransmembrane\b", r"\bcell surface\b"],
      "reject": [r"mitochondri", r"\bnucle", r"lysosom", r"endosom", r"\ber\b", r"endoplasmic", r"golgi",
                 r"\bsecreted\b", r"\bextracellular\b", r"\bcytoplasm\b", r"\bcytosol", r"single pass",
                 r"peripheral", r"vacuol", r"chloroplast", r"thylakoid", r"organelle", r"vesic", r"melanosom",
                 r"peroxisom"],
      "key": "plasma membrane (multi-pass)"}
LYSO = {"accept": [r"lysosom", r"endosom", r"endolysosom", r"melanosom", r"acidic (organelle|compartment|store)"],
        "reject": [r"plasma membrane", r"cell membrane", r"cell surface", r"mitochondri", r"\bnucle", r"\ber\b",
                   r"endoplasmic", r"golgi", r"\bsecreted\b", r"\bextracellular\b", r"\bcytosol"],
        "key": "late endosome / lysosome membrane"}

# ---- Q2 class ----------------------------------------------------------------------------------
CHANNEL = {"accept": [r"\bchannels?\b"],
           "reject": [r"transporter", r"\bpumps?\b", r"\bgpcr\b", r"g protein coupled", r"\benzyme\b",
                      r"exchanger", r"\bkinase\b"],
           "key": "ion channel"}

# ---- Q4 activating signal: shared vocabulary ---------------------------------------------------
V = [r"\bvoltage", r"\bdepolari", r"membrane potential"]
HYP = [r"hyperpolari"]
CNUC = [r"\bcamp\b", r"cyclic amp", r"cyclic nucleotide", r"\bcgmp\b", r"cyclic gmp"]
CA = [r"calcium", r"\bca2?\b", r"\bca2? i\b", r"\bcai\b"]
NA = [r"sodium", r"\bna\b", r"\bna i\b", r"\bnai\b"]
HEAT = [r"\bheat", r"\bwarm", r"\bhot\b"]
COLD = [r"\bcold", r"\bcool", r"menthol", r"icilin"]
TEMP = [r"temperatur", r"thermal", r"\bthermo"]
OSMO = [r"hypoton", r"osmo", r"swell", r"mechan", r"stretch", r"shear", r"pressure"]
IRR = [r"electrophil", r"irritant", r"mustard", r"\baitc\b", r"isothiocyanate", r"cinnamaldehyde", r"allicin",
       r"garlic", r"wasabi", r"reactive", r"acrolein", r"noxious chemical"]
NAADP = [r"naadp", r"nicotinic acid adenine"]
PI35 = [r"\bpi 3 5 p2\b", r"\bpi35p2\b", r"ptdins 3 5", r"phosphatidylinositol 3 5", r"3 5 bisphosphate"]
CAPS = [r"capsaicin", r"vanilloid"]
VTRP = [r"2 apb", r"camphor", r"carvacrol", r"thymol", r"eugenol"]
V4CHEM = [r"phorbol", r"4 alpha pdd", r"4apdd", r"4a pdd", r"gsk1016790a", r"arachidonic", r"\beets?\b",
          r"epoxyeicosatrienoic", r"\blow ph\b", r"citrate"]
CHEM = [r"\bchemical", r"\bcompound", r"\bligand", r"\bagonist"]


def act(key, accept, reject):
    return {"key": key, "accept": accept, "reject": reject}


# ---- Q5 partners: one group per UniProt-named partner gene (aliases); 2 groups named = full credit --
CALM = [r"calmodulin", r"\bcam\b", r"\bcalm[1-3]?\b"]


def g(*patterns):
    return list(patterns)


PROTEINS = {
    "KCNQ1": dict(acc="P51787", name="KCNQ1 (Kv7.1)", q1=PM, q3=6,
                  q4=act("voltage (depolarization)", V, HYP + CNUC + NA + HEAT + COLD + OSMO + IRR + NAADP + CAPS),
                  q5=[g(*CALM), g(r"\bkcne1?\b", r"\bmink\b", r"\bisk\b"), g(r"\bkcne2\b", r"\bmirp1\b"),
                      g(r"\bkcne3\b", r"\bmirp2\b"), g(r"\bkcne4\b"), g(r"\bkcne5\b", r"\bkcne1l\b"),
                      g(r"\bakap ?9\b", r"yotiao", r"\bakap ?450\b", r"\bakap\b"), g(r"\bnedd4 ?l\b", r"\bnedd4 2\b"),
                      g(r"\bap2m1\b", r"\bap ?2\b"), g(r"\busp2\b"), g(r"\bslc5a3\b", r"\bsmit1?\b"),
                      g(r"\bkcnq5\b", r"\bkv7 5\b")]),
    "KCND3": dict(acc="Q9UK17", name="KCND3 (Kv4.3)", q1=PM, q3=6,
                  q4=act("voltage (depolarization)", V, HYP + CNUC + CA + NA + HEAT + COLD + OSMO + IRR + NAADP + CAPS),
                  q5=[g(r"\bkcnd2\b", r"\bkv4 2\b"), g(r"\bkcnd1\b", r"\bkv4 1\b"),
                      g(r"\bkcnip1?\b", r"\bkchip1?\b", r"kv channel interacting"), g(r"\bkcnip2\b", r"\bkchip2\b"),
                      g(r"\bkcnip3\b", r"\bkchip3\b", r"calsenilin", r"\bdream\b"), g(r"\bkcnip4\b", r"\bkchip4\b"),
                      g(r"\bkcne1\b", r"\bmink\b"), g(r"\bkcne2\b", r"\bmirp1\b"), g(r"\bscn1b\b", r"\bnav ?beta ?1\b"),
                      g(r"\bkcnab1\b", r"\bkv ?beta ?1\b"), g(r"\bdlg1\b", r"\bsap97\b"),
                      g(r"\bdpp6\b", r"\bdppx\b", r"dipeptidyl (amino)?peptidase like"), g(r"\bdpp10\b", r"\bdppy\b")]),
    "HCN4": dict(acc="Q9Y3Q4", name="HCN4", q1=PM, q3=6,
                 q4=act("hyperpolarization (+ cAMP)", HYP + CNUC,
                        [r"\bdepolari"] + CA + NA + HEAT + COLD + OSMO + IRR + NAADP + CAPS),
                 q5=[g(r"\bpex5l\b", r"\btrip8b\b"), g(r"\birag1\b", r"\bmrvi1\b"), g(r"\birag2\b", r"\blrmp\b", r"\bjaw1\b")]),
    "KCNT1": dict(acc="Q5JUK3", name="KCNT1 (Slo2.2)", q1=PM, q3=6,
                  q4=act("intracellular Na+", NA, CA + HYP + CNUC + HEAT + COLD + OSMO + IRR + NAADP + CAPS),
                  q5=[g(r"\bkcnt2\b", r"\bslo2 1\b", r"\bslick\b"), g(r"\bfmr1\b", r"\bfmrp\b"), g(r"\bcrbn\b", r"cereblon")]),
    "KCNMA1": dict(acc="Q12791", name="KCNMA1 (BK)", q1=PM, q3=7,
                   q4=act("intracellular Ca2+ and/or depolarization", CA + V,
                          NA + HYP + CNUC + HEAT + COLD + OSMO + IRR + NAADP + CAPS),
                   q5=[g(r"\brab11b\b"), g(r"\bkcnmb1?\b", r"\bbk ?beta ?1?\b", r"\bslo ?beta"), g(r"\bkcnmb2\b", r"\bbk ?beta ?2\b"),
                       g(r"\bkcnmb3\b", r"\bbk ?beta ?3\b"), g(r"\bkcnmb4\b", r"\bbk ?beta ?4\b"),
                       g(r"\blrrc ?26\b", r"\blrrc\b", r"\bbk ?gamma"), g(r"\blrrc ?38\b"), g(r"\blrrc ?52\b"), g(r"\blrrc ?55\b")]),
    "TRPV3": dict(acc="Q8NET8", name="TRPV3", q1=PM, q3=6,
                  q4=act("warm / heat", HEAT + TEMP + VTRP, COLD + OSMO + NA + NAADP + CAPS + HYP + CNUC),
                  q5=[g(r"\btrpv1\b", r"\bvr1\b", r"capsaicin receptor"), g(r"\bsnx11\b", r"sorting nexin 11")]),
    "TRPV4": dict(acc="Q9HBA0", name="TRPV4", q1=PM, q3=6,
                  q4=act("hypotonic cell swelling / mechanical (also heat)", OSMO + HEAT + TEMP + V4CHEM,
                         COLD + CAPS + NA + NAADP + HYP + CNUC + IRR),
                  q5=[g(*CALM), g(r"\bmap7\b"), g(r"\blyn\b"), g(r"\bsrc\b"), g(r"\bfyn\b"), g(r"\bhck\b"), g(r"\blck\b"),
                      g(r"\byes1?\b"), g(r"\bctnnb1\b", r"beta catenin"), g(r"\bcdh1\b", r"e cadherin"),
                      g(r"\bpacsin ?[1-3]?\b", r"syndapin"), g(r"\bitpr3\b", r"\bip3 ?r"), g(r"\baqp5\b", r"aquaporin 5"),
                      g(r"\baqp4\b", r"aquaporin 4"), g(r"\bano1\b", r"\btmem16a\b", r"anoctamin 1"),
                      g(r"\bpkd2\b", r"polycystin 2", r"\btrpp2\b"), g(r"\bddx3x?\b"), g(r"\bmlc1\b"), g(r"\bhepacam\b"),
                      g(r"\batp1b1\b")]),
    "TRPM8": dict(acc="Q7Z2W7", name="TRPM8", q1=PM, q3=6,
                  q4=act("cold / menthol", COLD + TEMP, HEAT + CAPS + NA + NAADP + HYP + CNUC + IRR),
                  q5=[g(r"\btcaf1\b", r"\bfam115a\b"), g(r"\btcaf2\b", r"\bfam115c\b")]),
    "TRPA1": dict(acc="O75762", name="TRPA1", q1=PM, q3=6,
                  q4=act("electrophilic irritants (e.g. mustard oil)", IRR + CHEM, NA + NAADP + HYP + CNUC + CAPS),
                  q5=[g(r"\btmem100\b"), g(r"\begln1\b", r"\bphd2\b")]),
    "TPCN2": dict(acc="Q8NHX9", name="TPCN2 (TPC2)", q1=LYSO, q3=12,
                  q4=act("NAADP / PI(3,5)P2", NAADP + PI35, HEAT + COLD + OSMO + IRR + CAPS + HYP + CNUC + NA),
                  q5=[g(r"\blrrk2\b"), g(r"\bhax1\b"), g(r"\bmtor\b"), g(r"\blsm12\b"), g(r"\btpcn1\b", r"\btpc1\b")]),
}

# answers the key accepts, used by the placeholder oracle and as the worked example's printed answers
ORACLE = {
    "KCNQ1": ("plasma membrane", "voltage-gated potassium channel", 6, "membrane depolarization", ["KCNE1", "calmodulin"]),
    "KCND3": ("plasma membrane", "voltage-gated potassium channel", 6, "membrane depolarization", ["KChIP2", "DPP6"]),
    "HCN4": ("plasma membrane", "cyclic nucleotide-gated cation channel", 6, "hyperpolarization", ["TRIP8b", "IRAG1"]),
    "KCNT1": ("plasma membrane", "potassium channel", 6, "intracellular sodium", ["KCNT2", "FMRP"]),
    "KCNMA1": ("plasma membrane", "potassium channel", 7, "intracellular calcium", ["KCNMB1", "LRRC26"]),
    "TRPV3": ("plasma membrane", "cation channel", 6, "warm temperature", ["TRPV1", "SNX11"]),
    "TRPV4": ("plasma membrane", "cation channel", 6, "hypotonic cell swelling", ["calmodulin", "PACSIN3"]),
    "TRPM8": ("plasma membrane", "cation channel", 6, "cold", ["TCAF1", "TCAF2"]),
    "TRPA1": ("plasma membrane", "cation channel", 6, "electrophilic irritants", ["TMEM100", "EGLN1"]),
    "TPCN2": ("lysosome membrane", "cation channel", 12, "NAADP", ["LRRK2", "MTOR"]),
}


def crop(src: Path, dst: Path, margin=40):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(int)
    red = (a[..., 0] > 90) & (a[..., 0] > a[..., 1] + 50) & (a[..., 0] > a[..., 2] + 50)
    ys, xs = np.nonzero(red)
    h, w = red.shape
    box = (max(xs.min() - margin, 0), max(ys.min() - margin, 0), min(xs.max() + margin, w), min(ys.max() + margin, h))
    bg = tuple(int(v) for v in np.median(a[:5].reshape(-1, 3), axis=0))
    c = im.crop(box)
    side = max(c.size)
    canvas = Image.new("RGB", (side, side), bg)
    canvas.paste(c, ((side - c.size[0]) // 2, (side - c.size[1]) // 2))
    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst)  # Pillow writes no text/EXIF chunks
    return canvas.size


def entry(gene, subset_note):
    p = PROTEINS[gene]
    return {"protein": p["name"], "uniprot": p["acc"], "note": subset_note,
            "Q1": p["q1"], "Q2": CHANNEL, "Q3": {"key": p["q3"]}, "Q4": p["q4"],
            "Q5": {"key": "any 2 UniProt-listed partners", "groups": p["q5"], "need": min(2, len(p["q5"]))}}


def answers(gene):
    q1, q2, q3, q4, q5 = ORACLE[gene]
    return {"Q1": q1, "Q2": q2, "Q3": q3, "Q4": q4, "Q5": q5}


def main():
    held_out = [g_ for g_ in PROTEINS if g_ != "KCNQ1"]
    order = held_out[:]
    random.Random(SEED).shuffle(order)
    item_map, truth, oracle = {}, {}, {}
    for i, gene in enumerate(order, 1):
        item = f"item{i:02d}"
        size = crop(SCREENS / f"{gene}.png", DATA / "items" / f"{item}.png")
        item_map[item] = {"gene": gene, "uniprot": PROTEINS[gene]["acc"], "size": size}
        truth[item] = entry(gene, "held out")
        oracle[item] = answers(gene)
    crop(SCREENS / "KCNQ1.png", DATA / "examples" / "example.png")
    (ROOT / "picture_task/tests/truth.json").write_text(json.dumps(truth, indent=1) + "\n")
    (ROOT / "picture_task/solution/answers.json").write_text(json.dumps(oracle, indent=1) + "\n")
    (ROOT / "gen/picture/item_map.json").write_text(json.dumps(item_map, indent=1) + "\n")
    print(json.dumps(item_map, indent=1))
    print("worked example answers:", json.dumps(answers("KCNQ1")))


if __name__ == "__main__":
    main()
