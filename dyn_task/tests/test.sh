#!/bin/bash
# Verifier entry point: scores /app/answers.json, writes /logs/verifier/reward.txt + metrics.json
mkdir -p /logs/verifier
python3 /tests/score.py /app/answers.json --truth /tests/truth.json --out /logs/verifier
