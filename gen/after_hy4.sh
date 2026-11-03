#!/bin/bash
# Unattended: waits for Hy4's first scored-job trial (runs/main/task__rLtym3q). If it timed out without an answer
# file, stops job `main` (whose remaining Hy4 trials would also run to the limit) and runs the 2 remaining Astra
# attempts as job `astra_rest`; Hy4 is rerun later by hand. If Hy4 was scored, job `main` continues untouched.
#   nohup caffeinate -ims gen/after_hy4.sh > runs/after_hy4.log 2>&1 &
cd "$(dirname "$0")/.." || exit 1
export PATH=/opt/homebrew/bin:$PATH
T=runs/main/task__rLtym3q

until [ -f "$T/verifier/metrics.json" ] || python3 -c "
import json, sys; r = json.load(open('$T/result.json')); sys.exit(0 if r.get('finished_at') else 1)" 2>/dev/null; do
  sleep 30
done
sleep 5
scored=$(python3 -c "
import json
try: print(json.load(open('$T/verifier/metrics.json')).get('file_error') is None)
except Exception: print(False)")
echo "$(date) Hy4 trial finished; scored=$scored"
[ "$scored" = "True" ] && { echo "Hy4 scored: job main continues"; exit 0; }

pkill -f "harbor run -c jobs/main.yaml"            # matches only the harbor processes, not this script
sleep 10
for c in $(docker ps --format '{{.Names}}' | grep '^task__'); do docker stop "$c" > /dev/null; done
echo "$(date) job main stopped after Hy4 timeout; containers: $(docker ps --format '{{.Names}}' | grep -c '^task__')"
export OPENROUTER_API_KEY="$(cat ~/.config/collinear/openrouter_key)"
.venv/bin/harbor run -c jobs/astra_rest.yaml > runs/astra_rest.log 2>&1
echo "$(date) astra_rest done: $(grep -E '^│' runs/astra_rest.log | tail -1)"
