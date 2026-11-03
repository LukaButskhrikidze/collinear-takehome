"""Build results.json from the run folders (brief deliverables).

    python3 gen/make_results.py

Per subset: null, cheap-tool (naive), best shortcut (depositor) and reference rewards (runs/baselines.json, measured
2026-10-25 before any model run). Per model, on the scored trials of job `main` plus earlier scored v2 trials: mean,
sd and range of the aggregate and per-subset rewards, outcome counts (refused and filtered included), cost. No-tools
runs from runs/no_tools/<model>_<n>/. Total spend from the OpenRouter key.
"""
import csv
import glob
import json
import statistics as st
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = {"gpt-6-astra (max)": "openai/gpt-6-astra", "hy4-preview": "tencent/hy4-preview"}
SCORED_V2_JOBS = {"main", "v2_hy4", "v2_hy4_try1_mac_slept"}  # v2 item set, after the freeze; `smoke` was the v1 pilot


def summary(rows):
    scored = [r for r in rows if r["outcome"] == "scored"]
    out = {"n_trials": len(rows), "outcomes": {o: sum(r["outcome"] == o for r in rows) for o in
           ("scored", "malformed", "timeout", "truncated", "refused", "content_filtered", "provider_error")},
           "cost_usd": round(sum(float(r["cost_usd"] or 0) for r in rows), 2)}
    for k in ("reward", "in_regime", "across_boundary"):
        xs = [float(r[k]) for r in scored if r[k]]
        out[k] = {"mean": round(st.mean(xs), 3), "sd": round(st.stdev(xs), 3) if len(xs) > 1 else None,
                  "min": min(xs), "max": max(xs)} if xs else None
    return out


def no_tools(model_id):
    runs = []
    for d in sorted(glob.glob(str(ROOT / f"runs/no_tools/{model_id.split('/')[-1]}_*"))):
        m = json.load(open(f"{d}/metrics.json")) if Path(f"{d}/metrics.json").exists() else None
        resp = json.load(open(f"{d}/response.json"))
        choice = (resp.get("choices") or [{}])[0]
        failed = "error" in resp or choice.get("finish_reason") == "error"   # provider_error: never scored as 0
        if failed:
            m = None
        runs.append({"run": Path(d).name, "outcome": "provider_error" if failed else "scored",
                     "reward": m and round(m["reward"], 3),
                     "per_subset": m and {k: round(v, 3) for k, v in m["per_subset"].items()},
                     "finish": choice.get("finish_reason"), "error": resp.get("error") or choice.get("error"),
                     "cost_usd": resp.get("usage", {}).get("cost")})
    xs = [r["reward"] for r in runs if r["outcome"] == "scored"]
    return {"runs": runs, "scored_mean": round(st.mean(xs), 3) if xs else None,
            "scored_sd": round(st.stdev(xs), 3) if len(xs) > 1 else None}


def main():
    baselines = json.load(open(ROOT / "runs/baselines.json"))
    trials = list(csv.DictReader(open(ROOT / "runs/trials.csv")))
    key = (Path.home() / ".config/collinear/openrouter_key").read_text().strip()
    req = urllib.request.Request("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {key}"})
    spend = json.loads(urllib.request.urlopen(req).read())["data"]["usage"]
    results = {
        "task": "experimental-ensemble-size-and-core (v2, frozen 7bdbebe 2026-10-25)",
        "baselines_per_subset": {name: baselines[k] for name, k in
                                 (("null", "null"), ("cheap_tool_naive", "naive"),
                                  ("best_shortcut_depositor", "depositor"), ("reference", "reference"))},
        "models": {name: {"agentic": summary([r for r in trials if r["model"] == name and r["job"] in SCORED_V2_JOBS]),
                          "no_tools": no_tools(mid)} for name, mid in MODELS.items()},
        "target": {"astra_below": 0.60, "hy4_below": 0.30},
        "total_spend_usd": round(spend, 2),
    }
    (ROOT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results["models"], indent=1)[:1500])


if __name__ == "__main__":
    main()
