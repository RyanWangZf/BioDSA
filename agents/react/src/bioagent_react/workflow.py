from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .client import ModelClient
from .prompts import SYSTEM_PROMPT_TEMPLATE


class ReActAgent:
    """Model → first code tool call → feedback loop from legacy ReAct."""

    def __init__(self, config: dict, workspace: Path):
        config.setdefault("system_prompts", {})["react_decision"] = SYSTEM_PROMPT_TEMPLATE
        self.config, self.workspace = config, Path(workspace)
        self.client, self.trajectory = ModelClient(config), []

    def run(self, item: dict) -> dict:
        data = [str(Path("/app") / value) for value in item.get("input_paths", [])]
        prompt = item["instruction"] + ("\nAvailable data:\n" + "\n".join(data) if data else "")
        code_history = item.get("code_history", "")
        if code_history:
            prompt += "\nRequired source context (already provided to every code execution):\n" + code_history
        messages = [{"role": "user", "content": prompt}]
        executions = []
        for turn in range(int(self.config.get("recursion_limit", 20))):
            decision = self.client.complete("react_decision", {"messages": messages, "turn": turn})
            if isinstance(decision, str):
                decision = json.loads(decision)
            self.trajectory.append({"event": "model_decision", "turn": turn, "decision": decision})
            calls = decision.get("tool_calls") or []
            if not calls:
                answer = decision.get("final_answer", "")
                self.trajectory.append({"event": "stop", "reason": "no_tool_calls"})
                return {"final_answer": answer, "trajectory": self.trajectory,
                        "usage": {"model_calls": len(self.client.calls), "tool_calls": len(executions)},
                        "artifacts": {"code_execution.json": executions}}
            # Legacy _tool_node intentionally executes only tool_calls[0].
            call = calls[0]
            if call.get("name") != "code_execution":
                raise ValueError(f"unsupported tool: {call.get('name')}")
            code = call.get("args", {}).get("code")
            if not isinstance(code, str):
                raise ValueError("code_execution requires string code")
            executed_code = "\n\n".join(part for part in (code_history, code) if part)
            completed = subprocess.run(
                [self.config.get("python_executable", sys.executable), "-c", executed_code],
                cwd=self.workspace, text=True, capture_output=True,
                timeout=float(self.config.get("code_timeout_seconds", 30)),
            )
            record = {"code": code, "executed_code": executed_code, "exit_code": completed.returncode,
                      "stdout": completed.stdout, "stderr": completed.stderr}
            executions.append(record)
            self.trajectory.append({"event": "tool_result", **record})
            messages.extend([{"role": "assistant", "content": decision},
                             {"role": "tool", "content": completed.stdout + completed.stderr}])
        raise RuntimeError("ReAct recursion limit reached")
