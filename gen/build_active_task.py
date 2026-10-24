"""Assemble task_active/ from the key: data folders, truth, per-receptor baselines, instruction.

    python gen/build_active_task.py <key.json> <source_dir> [<source_dir> ...]

key.json rows: [protein_id, subset, pdb_id, active, partner, d_min, d_max]; subset is
'example', 'in_regime' or 'across_boundary'. Only keyed entries are shipped. The baseline error
per receptor is the error of the best shortcut on exactly the shipped entries (file-based
shortcuts in task_active/baseline/shortcuts.py, and the G-protein shortcut using GPCRdb's curated
partner field), floored at 1.
"""
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "task_active"
key = json.load(open(sys.argv[1]))
sources = [Path(s) for s in sys.argv[2:]]


def source_of(acc):
    for s in sources:
        if (s / acc / "uniprot.fasta").exists():
            return s / acc
    raise SystemExit(f"no source folder for {acc}")


by = defaultdict(list)
ideal = defaultdict(int)          # 'G protein / arrestin bound' shortcut using GPCRdb's curated partner field
for acc, subset, pdb, lab, partner, *_ in key:
    by[(acc, subset)].append((pdb, lab))
    ideal[acc] += (partner != "none") != bool(lab)

data = TASK / "environment" / "data"
for sub in ("proteins", "examples"):
    shutil.rmtree(data / sub, ignore_errors=True)
truth, receptors, table = [], [], []
for (acc, subset), entries in sorted(by.items()):
    dest = data / ("examples" if subset == "example" else "proteins") / acc
    (dest / "structures").mkdir(parents=True)
    src = source_of(acc)
    shutil.copy(src / "uniprot.fasta", dest / "uniprot.fasta")
    for pdb, lab in sorted(entries):
        shutil.copy(src / "structures" / f"{pdb}.cif.gz", dest / "structures" / f"{pdb}.cif.gz")
    if subset == "example":
        with open(dest / "answer.csv", "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["protein_id", "pdb_id", "active"])
            w.writerows((acc, pdb, lab) for pdb, lab in sorted(entries))
        continue
    truth += [(acc, pdb, lab) for pdb, lab in sorted(entries)]
    header = (src / "uniprot.fasta").read_text().split("\n", 1)[0]
    name, org = header.split(" ", 1)[1].split(" OS=")[0], header.split(" OS=")[1].split(" OX=")[0]
    table.append((acc, name, org, len(entries)))
    receptors.append([acc, subset])

# per-receptor baseline error = best shortcut on the shipped entries
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run([sys.executable, "-I", str(TASK / "baseline" / "shortcuts.py"), str(data / "proteins"), tmp], check=True)
    preds = {}
    for f in Path(tmp).glob("*.csv"):
        preds[f.stem] = {(r["protein_id"], r["pdb_id"]): int(r["active"]) for r in csv.DictReader(open(f))}
for r in receptors:
    ks = [(a, p, l) for a, p, l in truth if a == r[0]]
    errs = {n: sum(p.get((a, pdb), 0) != l for a, pdb, l in ks) for n, p in preds.items()}
    errs["gprotein_curated"] = ideal[r[0]]
    r += [max(min(errs.values()), 1), json.dumps(errs, sort_keys=True)]

tests = TASK / "tests"
with open(tests / "truth.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["protein_id", "pdb_id", "active"]); w.writerows(truth)
with open(tests / "receptors.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["protein_id", "subset", "baseline_error", "shortcut_errors"]); w.writerows(receptors)
rows = "\n".join(f"| {a} | {n} | {o} | {k} |" for a, n, o, k in table)
(TASK / "instruction.md").write_text((TASK / "instruction.template.md").read_text().replace(
    "{TABLE}", "| protein_id | Receptor | Organism | Structures |\n|---|---|---|---|\n" + rows))
for r in receptors:
    print(r)
print(f"truth rows: {len(truth)}")
