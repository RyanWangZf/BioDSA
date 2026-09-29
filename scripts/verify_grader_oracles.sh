#!/usr/bin/env bash
set -u

root=$(cd "$(dirname "$0")/.." && pwd)
work=${TMPDIR:-/tmp}/bioagent-gym-grader-oracles
python3 "$root/scripts/prepare_grader_oracles.py" --bio-output "$work/bio" --deep-output "$work/deep"

bio_task="$root/benchmarks/biodsbench/tasks/biodsbench-python"
docker build -q -t bioagent-gym-biodsbench-oracle -f "$bio_task/tests/Dockerfile" "$bio_task/tests" >/dev/null
rm -rf "$work/bio/logs"; mkdir -p "$work/bio/logs"
docker run --rm --network none \
  -v "$work/bio/submission:/app/submission:ro" -v "$work/bio/logs:/logs" \
  bioagent-gym-biodsbench-oracle /tests/test.sh || true
cat "$work/bio/logs/verifier/summary.json"
python3 "$root/scripts/prepare_biodsbench_mutants.py" --output "$work/bio-mutants"
mkdir -p "$work/bio-mutants/logs"
docker run --rm --network none \
  -v "$work/bio-mutants/submission:/app/submission:ro" -v "$work/bio-mutants/logs:/logs" \
  bioagent-gym-biodsbench-oracle /tests/test.sh
cat "$work/bio-mutants/logs/verifier/summary.json"

for task in "$root"/benchmarks/biomedicine-deep-research/tasks/*; do
  name=${task##*/}; image="bioagent-gym-bdr-oracle-$name"; logs="$work/deep/$name/logs"
  docker build -q -t "$image" -f "$task/tests/Dockerfile" "$task/tests" >/dev/null
  rm -rf "$logs"; mkdir -p "$logs"
  docker run --rm --network none \
    -v "$work/deep/$name/submission:/app/submission:ro" -v "$logs:/logs" \
    "$image" /tests/test.sh || true
  printf '%s ' "$name"; cat "$logs/verifier/summary.json"
done

printf 'Oracle artifacts: %s\n' "$work"
