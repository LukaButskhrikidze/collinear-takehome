"""Choose a smaller entry subset for one protein (generator side, never shipped).

    python3 choose.py <compare.json> <proteins_dir> ACC N_TOTAL N_TRAP SEED [--write <dest_dir>]

Only "clean" entries (my pipeline's copies == reference copies, gen/subset/compare.py) are eligible, so the
answer key does not hinge on a mapping judgement call. N_TRAP of them are "traps" (the entry's own
_struct_ref_seq mapping disagrees with the sequence). Prints, on the subset, the reference, depositor,
naive and null answers. --write copies the chosen mmCIFs + uniprot.fasta to <dest_dir>/<ACC>/.
"""
import json
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "task" / "solution"))
sys.path.insert(0, str(ROOT / "task" / "baseline"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reference as R  # noqa: E402
import naive as N  # noqa: E402
from compare import counts, depositor_members  # noqa: E402


def evaluate(folder, pdbs, acc):
    uni = R.read_fasta(folder / "uniprot.fasta")
    files = [f for f in sorted((folder / "structures").glob("*.cif*")) if f.name.split(".")[0].lower() in pdbs]
    ref, dep, nai = [], [], []
    for f in files:
        ref += R.entry_members(f, uni)
        dep += depositor_members(f, acc)
        nai += N.entry_members_naive(f, uni)
    return {"reference": counts(ref), "depositor": counts(dep), "naive": counts(nai),
            "null": {"n_members": len(files), "n_core": len(uni)}}


def main():
    cmp_json, proteins_dir, acc, n_total, n_trap, seed = sys.argv[1:7]
    n_total, n_trap, seed = int(n_total), int(n_trap), int(seed)
    entries = json.load(open(cmp_json))[acc]
    clean = [e for e in entries if e["clean"] and e["n_ref"] > 0]
    traps = sorted(e["pdb"] for e in clean if e["trap"])
    plain = sorted(e["pdb"] for e in clean if not e["trap"])
    rng = random.Random(seed)
    pick = rng.sample(traps, min(n_trap, len(traps)))
    pick += rng.sample(plain, min(n_total - len(pick), len(plain)))
    pick = sorted(pick)
    folder = Path(proteins_dir) / acc
    res = evaluate(folder, set(pick), acc)
    print(json.dumps({"acc": acc, "seed": seed, "n_entries": len(pick), "n_traps": sum(p in traps for p in pick),
                      **res, "entries": pick}))
    if "--write" in sys.argv:
        dest = Path(sys.argv[sys.argv.index("--write") + 1]) / acc
        (dest / "structures").mkdir(parents=True, exist_ok=True)
        shutil.copy(folder / "uniprot.fasta", dest / "uniprot.fasta")
        for f in sorted((folder / "structures").glob("*.cif*")):
            if f.name.split(".")[0].lower() in pick:
                shutil.copy(f, dest / "structures" / f.name)


if __name__ == "__main__":
    main()
