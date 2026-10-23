#!/bin/bash
# Reference solution: answers from /app/data alone, same container, well inside 60 minutes
# (pilot: 4 proteins in ~4 s, ~210 MB RAM).
set -euo pipefail
python3 "$(dirname "$0")/reference.py" /app/data/proteins /app/answers.csv
