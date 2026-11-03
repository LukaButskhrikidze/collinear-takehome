"""Recompute members/core with my pipeline's CURRENT code, in memory only (writes nothing)."""
import importlib, json, os, sys
from pathlib import Path

P = os.environ["PIPELINE_PKG"]   # my pipeline's Python package, importable in its own venv
load_catalog = importlib.import_module(f"{P}.catalog.schema").load_catalog
load_ensemble_entities = importlib.import_module(f"{P}.ensemble.entity").load_ensemble_entities
filter_entities = importlib.import_module(f"{P}.ensemble.filter").filter_entities
_align = importlib.import_module(f"{P}.ensemble.align")
align_filtered, AlignSkip = _align.align_filtered, _align.AlignSkip

root = Path(sys.argv[1])
cat = load_catalog(root)
wanted = set(sys.argv[2:])
ens_list = [e for e in cat.ensembles if e.uniprot in wanted and e.kind == "monomer"]
for e in ens_list:
    side = json.load(open(root / "products" / e.uniprot / "monomer" / "sidecar.json"))
    ents = load_ensemble_entities(root, e)
    filt = filter_entities(ents)
    fit = align_filtered(filt)
    if isinstance(fit, AlignSkip):
        print(e.uniprot, "SKIP", fit.reason); continue
    core = fit.members[0].core_res
    print(f"{e.uniprot}: current code -> members={len(fit.members)} unaligned={len(fit.unaligned)} core={len(core)} | "
          f"sidecar -> members={len(side['models'])} unaligned={len(side.get('unaligned') or [])} core={len(side['core_residues'])} "
          f"reasons={[u.get('reason') for u in (side.get('unaligned') or [])]} | now unaligned reasons={[u.reason for u in fit.unaligned][:3]}")
