"""No-tools runs (brief 2.6): the one-prompt version of the task through the plain chat API, scored by the verifier.

    python3 gen/no_tools_run.py <model> <n_runs> [prompt.md] [out_dir]

Same reasoning settings as the agent runs and each model's maximum output (Astra: effort max, 128k tokens; Hy4:
default, 64k). Each run saves the raw response, the CSV it contains (the last block that starts with the header
line) and the verifier's reward.txt / metrics.json. The key is read from ~/.config/collinear/openrouter_key and
never printed.
"""
import json
import re
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER = "protein_id,n_members,n_core"


def ask(model, prompt, key):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "usage": {"include": True},
            "max_tokens": 128000 if "astra" in model else 64000}
    if "astra" in model:
        body["reasoning"] = {"effort": "max"}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=3600) as r:
            resp = json.loads(r.read())
    except Exception as exc:  # classified as provider_error in trials.csv, never scored as a wrong answer
        resp = {"error": str(exc)}
    resp["_elapsed_s"] = round(time.time() - t0, 1)
    return resp


def extract_csv(text):
    """The reply's CSV: the last block after a header line; if the reply has no header but its lines are all
    `<id>,<int>,<int>` rows (Hy4 answered that way), the header is added. Anything else gives an empty file,
    which the verifier scores 0 with the reason."""
    lines = [ln.strip() for ln in text.replace("```csv", "").replace("```", "").splitlines()]
    starts = [i for i, ln in enumerate(lines) if ln.replace(" ", "") == HEADER]
    if not starts:
        rows = [ln for ln in lines if ln]
        if rows and all(re.fullmatch(r"[A-Z0-9]{6,10}\s*,\s*\d+\s*,\s*\d+", ln) for ln in rows):
            return HEADER + "\n" + "\n".join(rows) + "\n"
        return ""
    block = [HEADER]
    for ln in lines[starts[-1] + 1:]:
        if not ln or "," not in ln:
            break
        block.append(ln)
    return "\n".join(block) + "\n"


def run_one(model, n, prompt, key, out_dir, rescore=False):
    d = out_dir / f"{model.split('/')[-1]}_{n}"
    d.mkdir(parents=True, exist_ok=True)
    if rescore:                                   # re-extract and re-score a saved reply, no API call
        resp = json.load(open(d / "response.json"))
    else:
        resp = ask(model, prompt, key)
        (d / "response.json").write_text(json.dumps(resp, indent=1))
    msg = (resp.get("choices") or [{}])[0].get("message") or {}
    (d / "answers.csv").write_text(extract_csv(msg.get("content") or ""))
    subprocess.run([sys.executable, str(ROOT / "task/tests/score.py"), str(d / "answers.csv"),
                    "--truth", str(ROOT / "task/tests/truth.csv"), "--out", str(d)], capture_output=True)
    reward = (d / "reward.txt").read_text().strip() if (d / "reward.txt").exists() else "n/a"
    finish = (resp.get("choices") or [{}])[0].get("finish_reason")
    return f"{d.name}: reward {reward}, finish {finish}, cost {resp.get('usage', {}).get('cost')}, " \
           f"{resp['_elapsed_s']} s{', error ' + resp['error'][:80] if 'error' in resp else ''}"


def main(model, runs, prompt_path=str(ROOT / "runs/no_tools/prompt.md"), out_dir=str(ROOT / "runs/no_tools"),
         rescore=""):
    """runs: a count ("3" -> runs 1-3) or explicit run numbers ("4" with a leading "=", e.g. "=4" or "=2,3")."""
    key = Path.home().joinpath(".config/collinear/openrouter_key").read_text().strip()
    prompt = Path(prompt_path).read_text()
    nums = [int(x) for x in runs[1:].split(",")] if runs.startswith("=") else range(1, int(runs) + 1)
    with ThreadPoolExecutor(len(nums)) as pool:
        for line in pool.map(lambda n: run_one(model, n, prompt, key, Path(out_dir), rescore == "rescore"), nums):
            print(line, flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:])
