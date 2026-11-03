# Item generation (outside the agent's container)

Read-only on my pipeline's data (on the pipeline host). No SLURM job is started without asking.

1. **Pick proteins:** `gen/pipeline_key.py` on the pipeline host prints, per accession, entries,
   members, unaligned, core (sidecar vs per-chain traces) and raw size.
2. **Copy inputs:** `gen/fetch_from_pipeline.sh task/environment/data/proteins ACC …`
   copies the exact raw mmCIFs + UniProt FASTA my pipeline used.
3. **Answer keys:** recompute with my pipeline after its regeneration; write
   `gen/pipeline_keys_<set>.tsv` (protein_id, subset, n_members, n_core, note).
4. **Shortcuts:** `task/baseline/null.py`, `task/baseline/naive.py` on the same folders.
5. **Truth + data card:** `python gen/make_truth.py gen/pipeline_keys_<set>.tsv null.csv naive.csv`
   → `task/tests/truth.csv` (with fixed baseline errors) and `gen/data_card.csv`.
6. **Cross-check:** `task/solution/reference.py`; keep a protein only if it agrees with
   my pipeline's key within the rubric floor, or the difference is explained (see PLAN.md §8).
7. **Anchor:** worked example P69441 (open/closed adenylate kinase, 4AKE/1AKE).
8. **No-tools prompt:** `gen/no_tools_prompt.py task/environment/data/proteins runs/no_tools/prompt.md`.
