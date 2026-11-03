"""Run my pipeline's CURRENT code in memory on a chosen subset of entries (writes nothing).

    <pipeline venv python> pipeline_subset.py <pipeline data root> <subsets.json> ACC [ACC ...]
subsets.json: {ACC: [pdb_id, ...]}; an ACC missing from it is run on all its entries.
"""
import importlib, json, os, sys
from pathlib import Path

P = os.environ["PIPELINE_PKG"]   # my pipeline's Python package, importable in its own venv
load_catalog = importlib.import_module(f"{P}.catalog.schema").load_catalog
load_ensemble_entities = importlib.import_module(f"{P}.ensemble.entity").load_ensemble_entities
filter_entities = importlib.import_module(f"{P}.ensemble.filter").filter_entities
_align = importlib.import_module(f"{P}.ensemble.align")
align_filtered, AlignSkip = _align.align_filtered, _align.AlignSkip

root = Path(sys.argv[1])
subsets = json.load(open(sys.argv[2]))
wanted = set(sys.argv[3:])
cat = load_catalog(root)
out = {}
for e in [e for e in cat.ensembles if e.uniprot in wanted and e.kind == "monomer"]:
    ents = load_ensemble_entities(root, e)
    keep = subsets.get(e.uniprot)
    if keep is not None:
        keep = {p.lower() for p in keep}
        ents = [x for x in ents if x.pdb_id.lower() in keep]
    fit = align_filtered(filter_entities(ents))
    if isinstance(fit, AlignSkip):
        out[e.uniprot] = {"skip": str(fit.reason)}
        continue
    out[e.uniprot] = {"n_entries": len({x.pdb_id for x in ents}), "n_copies": len(ents),
                      "n_members": len(fit.members), "n_unaligned": len(fit.unaligned),
                      "n_core": len(fit.members[0].core_res)}
print(json.dumps(out))
