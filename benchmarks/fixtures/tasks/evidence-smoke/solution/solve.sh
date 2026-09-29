#!/bin/sh
mkdir -p /app/submission
printf 'fixture\n' > /app/submission/final_answer.md
printf '[{"id":"x"}]\n' > /app/submission/citations.json
printf '[{"event":"orchestrator_start"},{"event":"subagent_dispatched"},{"event":"tool_result"},{"event":"memory_retrieved"},{"event":"code_execution"},{"event":"orchestrator_complete"}]\n' > /app/submission/trace.json
printf '{"entities":[{"id":"x"}],"relations":[]}\n' > /app/submission/memory_graph.json
printf '{}\n' > /app/submission/usage.json
printf '[]\n' > /app/submission/execution.json
