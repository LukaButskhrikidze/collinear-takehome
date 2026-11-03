#!/bin/bash
# PLACEHOLDER oracle for the pilot: copies the UniProt answer key so the verifier and the
# Harbor wiring can be checked end to end. Not a valid reference under the brief (an answer
# file from environment/data alone): no script can read a protein's identity off a picture.
set -euo pipefail
cp "$(dirname "$0")/answers.json" /app/answers.json
