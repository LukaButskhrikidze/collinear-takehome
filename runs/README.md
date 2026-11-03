# Runs

Harbor job folders go here (trim long agent logs; keep `result.json` and `verifier/`
for every trial), plus `trials.csv`, `baselines.json` and `no_tools/`.

## trials.csv — one row per trial

`model, job, trial, outcome, reward, in_regime, across_boundary, cost_usd, failure_class, note`

**outcome** (exactly one per trial, brief 2.2):

| outcome | meaning | how we tell |
|---|---|---|
| scored | agent wrote `/app/answers.csv` and the verifier scored it, including 0 | `verifier/metrics.json` has `file_error: null` |
| malformed | agent wrote something the verifier rejected | `file_error` = header / unreadable |
| timeout | agent hit the 3600 s limit | Harbor timeout exception in `result.json` |
| truncated | a response was cut at the token/context limit and never recovered | opencode log: length stop, no answer after |
| refused | the model declined | transcript |
| content_filtered | provider blocked request or response | OpenRouter error / finish reason |
| provider_error | any other API failure, incl. out of credit | `result.json` exception |

**failure_class** (scored trials that lost reward, brief 2.2.5):
`construct` (wrong biology: kept fusion/tag/partner residues, author numbering, dropped
mutants, …), `harness` (environment/tool problem), `format` (answer shape), `bookkeeping` (no-tools
only: interval/set arithmetic done by hand went wrong, in-regime items included, so not the named biology). Only
`construct` losses count toward the target; fix harness/format causes and rerun.

**Validity check:** if non-scored trials are more than a third of all trials, the
target is not shown.
