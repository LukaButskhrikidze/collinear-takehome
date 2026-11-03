# Pre-flight report — experimental-ensemble task (2026-10-23)

Status: **pilot built and passing in Harbor** (4 proteins). Docker image builds (34 s);
Harbor 0.20.0 oracle = **0.981**; agent-phase network allowlist verified. No model run yet.

## 1. The task (what the agent sees: `task/instruction.md`)

For each protein, the agent gets its UniProt FASTA and every PDB entry that contains
it (raw mmCIF, snapshot 2026-08-30). It must build the protein's experimental monomer
ensemble and report two numbers:

- `n_members`: protein copies in the ensemble;
- `n_core`: UniProt positions present (with a Cα) in every member.

| protein_id | Protein | Entries | Subset |
|---|---|---|---|
| P69441 | E. coli adenylate kinase | 29 | worked example (55 / 181 given) |
| O66490 | A. aeolicus adenylate kinase | 14 | in_regime |
| P43408 | M. igneus adenylate kinase | 3 | in_regime |
| P07550 | β2-adrenergic receptor | 130 | across_boundary |
| P29274 | A2A adenosine receptor | 188 | across_boundary |

- **Pinned** (`name = value unit` lines): first model, first altloc, copy overlap 10,
  min fraction 0.80, Cα fit 2.0 Å / 5 cycles / 8.0 Å fallback, reference = shortest,
  core definition, UniProt numbering.
- **Free — the biology:** what is protein; which segments are this UniProt protein
  (tags, linkers, T4L/BRIL fusions, G proteins, nanobodies, antibodies are not);
  mapping author numbering to UniProt; mutants and ligand-bound structures count.
- **Mechanism (across_boundary):** crystallisation constructs carry non-native parts and
  non-UniProt numbering; the ensemble only works after stripping them.

## 2. Ground truth

- Answer key = my pipeline (SIFTS + numbering audit). Same environment as the pipeline's:
  Python 3.9, gemmi 0.7.5, numpy 2.0.2, scipy 1.13.1, PyYAML 6.0.3.
- Independent cross-check = `task/solution/reference.py` (my code, same packages,
  sequence alignment to UniProt instead of SIFTS).

Per-protein values (key, reference, naive, null) are in `gen/answers_private.md`
(local only, never pushed). Summary: the reference matches my pipeline's key exactly on 3 of 4
pilot proteins and on all member counts; naive matches on the in-regime proteins and is
far off on both receptors.

## 3. Rubric (`task/tests/metric.py`, same file the agent gets)

- Each number: `clip(1 − |pred − truth| / baseline_error, 0, 1)`.
- `baseline_error` = error of the **best cheap method** (null or naive), floored at
  1 (members) or max(1, 5% of truth) (core). Fixed per protein in `tests/truth.csv`.
- Protein = 0.25 × members + 0.75 × core. Task = mean over proteins; per-subset too.
- Why weighted: counting files nearly equals `n_members` for receptors, so members alone
  gave 0.49 free points; with this rubric that shortcut scores 0.

| | in_regime | across_boundary | all |
|---|---|---|---|
| null | 0.40 | **0.00** | 0.20 |
| naive (cheap tool) | 1.00 | **0.00** | 0.50 |
| reference | 1.00 | 0.96 | **0.98** (≥ 0.8 ✓) |

Verifier tested: perfect 1.0; missing file, bad header, empty file → 0 with reason;
duplicate / missing / non-integer rows → 0 for that protein, kept in denominator;
`24.0` accepted as 24.

## 4. Harbor (checked against v0.20.0 source)

```
Collinear/
  task/  task.toml  instruction.md  spec.yaml
         environment/Dockerfile  environment/data/{metric.py, examples/P69441, proteins/…} (64 MB)
         tests/{test.sh, score.py, metric.py, truth.csv}   solution/{solve.sh, reference.py}
         baseline/{null.py, naive.py, README.md}
  gen/   fetch_from_pipeline.sh  pipeline_key.py  pipeline_recompute.py  make_truth.py  no_tools_prompt.py
         (local only: pipeline_keys_*.tsv, data_card.csv, answers_private.md)
  jobs/  oracle.yaml  smoke.yaml  main.yaml (Appendix B agents block as given)
  runs/  README.md (outcome table)  trials.csv  baselines.json  no_tools/prompt.md
```

- `task.toml` schema 1.1; agent 3600 s; verifier 300 s; 3 CPU / 6144 MB / no GPU.
- Paths: tests → `/tests`, solution → `/solution`, reward → `/logs/verifier/reward.txt`
  (+ `metrics.json`); answer at `/app/answers.csv`.
- **Network:** agent phase allow-list = `openrouter.ai`, `models.dev` only (no RCSB /
  SIFTS / UniProt lookups, no pip). opencode installs before the switch, on public network.
- Dockerfile sets `OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX=64000`; installs curl for opencode.
- Jobs: `retry.max_retries: 0` (every trial counted once), `n_concurrent_trials: 1`.

## 5. Compute

- Reference: 4 proteins in **4 s, 210 MB RAM**; adenylate kinase alone 0.7 s.
  3 CPUs / 6 GB is far more than the task needs; the agent's thinking time dominates.
- Docker runs in **colima: 4 CPUs, 8 GB** → exactly one trial at a time (hence
  `n_concurrent_trials: 1`). Harbor's default of 4 would starve trials → fake timeouts.
- Protein size: keep UniProt length ≤ ~500 and ≤ ~200 entries per protein; the pilot's
  largest (A2A, 412 aa, 188 entries, 27 MB) runs in ~2 s. Total data now 64 MB.
- Brief cost note: an Astra trial ≈ $4–18. Smoke first (1 Astra + 1 Hy4).

## 6. Outcome table (brief 2.2)

`runs/README.md` defines the 7 outcomes (scored / malformed / timeout / truncated /
refused / content_filtered / provider_error), how each is detected, the failure classes
(construct / harness / format), and the "> 1/3 non-scored = not shown" rule.
`runs/trials.csv` has the header ready.

## 7. No-tools version

`runs/no_tools/prompt.md`: same question, sequences + observed Cα positions instead of
coordinates; **62,681 chars ≈ 15.7k tokens** — fits Astra and Hy4.

## 8. Open issues — decide before freezing

1. ~~The pipeline's core definition~~ — **resolved.** The code and README agree (core over aligned
   members). The on-disk sidecars of P07550 and P16304 are **stale**: written by an older
   code version ("flagged numbering" members, a rule no longer in the code) and never
   rewritten because of her fingerprint skip. Keys now come from her *current* code run in
   memory (`gen/pipeline_recompute.py`), not from sidecars.
2. **Regeneration:** align stage finished 2026-10-22 21:08, no jobs running; TM-scores
   not recomputed (not needed for this task).
3. **Two GT judgement calls found** (good report material):
   - 8pvw (adenylate kinase with the LID domain replaced): the pipeline numbers the junction Gly
     as UniProt 151; the reference calls it non-native → core differs by 1.
   - P07550: SIFTS segments stop earlier than the sequence match at fusion junctions
     and C-termini (5d6l, 7dhr, 8gej …) → core differs by 9.
4. **More items needed:** pilot is 2 + 2. Target ~6 + 6, chosen by
   `gen/pipeline_key.py` + `gen/fetch_from_pipeline.sh`; boundary = construct-heavy (GPCR fusions,
   MBP fusions, polyprotein numbering); keep only proteins where the pipeline and the reference
   agree within the floor.
5. **Network allow-list** is enforced by Harbor's egress sidecar; confirm in the smoke run
   that opencode starts and that `curl https://www.rcsb.org` fails inside the agent phase.
6. **Freeze:** `git init` in `Collinear/`, commit `task/spec.yaml` + `tests/truth.csv`
   before the first model run.

## 9. Run order

Done (2026-10-23):
- Harbor 0.20.0 in `Collinear/.venv`; `docker-buildx` installed (Harbor needs it for the
  network sidecar).
- `harbor run -c jobs/oracle.yaml` → **0.981**, 42 s, 0 exceptions (`runs/oracle/`).
- Network check (`runs/network_check.txt`): RCSB, EBI/SIFTS, UniProt, PyPI, GitHub blocked;
  openrouter.ai and models.dev reachable.

Caveat: colima only shares the home folder with Docker, so tasks and `jobs_dir` must live
under `/Users/...` (a run from `/private/tmp` silently loses its log mounts).

Next (costs money, needs `OPENROUTER_API_KEY`):
```bash
export OPENROUTER_API_KEY=...
.venv/bin/harbor run -c jobs/smoke.yaml   # 1 Astra + 1 Hy4
.venv/bin/harbor run -c jobs/main.yaml    # 3 + 3, after freezing (git commit)
```
