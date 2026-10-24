#!/bin/bash
# Reference solution: labels from /app/data alone, same container, well inside 60 minutes.
set -euo pipefail
python3 "$(dirname "$0")/reference_active.py" /app/data/proteins /app/answers.csv
