#!/bin/sh
set -eu
mkdir -p /app/submission
printf 'fixture completed\n' > /app/submission/final_answer.md
printf '{"status":"ok"}\n' > /app/submission/artifact.json
