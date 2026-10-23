#!/bin/bash
# Verifier entry point: scores /app/answers.csv, writes /logs/verifier/reward.txt + metrics.json
mkdir -p /logs/verifier
python3 /tests/score.py /app/answers.csv --truth /tests/truth.csv --out /logs/verifier
