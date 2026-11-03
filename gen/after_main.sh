#!/bin/bash
# Runs unattended after the scored job: waits for `harbor run -c jobs/main.yaml` to exit, then adds Hy4 attempts
# (one at a time, at most 3 extra) until job `main` plus the extras hold 3 scored Hy4 trials, then rebuilds
# results.json. Every attempt, timed out or not, stays in runs/ and goes into trials.csv.
#   nohup caffeinate -ims gen/after_main.sh > runs/after_main.log 2>&1 &
cd "$(dirname "$0")/.." || exit 1
export PATH=/opt/homebrew/bin:$PATH
export OPENROUTER_API_KEY="$(cat ~/.config/collinear/openrouter_key)"

while pgrep -f "harbor run -c jobs/main.yaml" > /dev/null; do sleep 60; done
echo "$(date) main finished"

hy4_scored() {   # scored = the verifier found an answer file (file_error null)
  python3 - <<'EOF'
import glob, json
n = 0
for t in glob.glob("runs/main/*/") + glob.glob("runs/hy4_extra_*/*/"):
    try:
        cfg = json.dumps(json.load(open(t + "config.json")))
        m = json.load(open(t + "verifier/metrics.json"))
    except Exception:
        continue
    n += "hy4-preview" in cfg and m.get("file_error") is None
print(n)
EOF
}

for i in 1 2 3; do
  n=$(hy4_scored)
  echo "$(date) Hy4 scored so far: $n"
  [ "$n" -ge 3 ] && break
  sed "s/^job_name: .*/job_name: hy4_extra_$i/" jobs/hy4_extra.yaml > "jobs/hy4_extra_$i.yaml"
  .venv/bin/harbor run -c "jobs/hy4_extra_$i.yaml" > "runs/hy4_extra_$i.log" 2>&1
  echo "$(date) extra attempt $i done: $(tail -8 "runs/hy4_extra_$i.log" | grep -E '^│' | tail -1)"
done

python3 gen/make_results.py > runs/make_results.log 2>&1
echo "$(date) results.json rebuilt; done"
