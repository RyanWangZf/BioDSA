from __future__ import annotations

import math
from pathlib import Path
from .client import ModelClient
from .prompts import RISKQA_SYSTEM_PROMPT
from .tools import bm25_rank, load_riskcalcs


class AgentMD:
    def __init__(self, config: dict, workspace: Path):
        config.setdefault("system_prompts", {}).update({stage: RISKQA_SYSTEM_PROMPT for stage in
            ("calculator_query", "select_calculator", "extract_inputs", "calculator_answer")})
        self.config, self.workspace = config, Path(workspace)
        self.client, self.trajectory = ModelClient(config), []

    def run(self, item: dict) -> dict:
        mode = self.config.get("retrieval_mode", "bm25")
        calculators = item.get("calculator_fixture")
        if calculators is None:
            path = self.config.get("riskcalcs_path")
            if not path or not Path(path).is_file():
                raise RuntimeError("RiskCalcs resource unavailable; configure calculator_fixture or riskcalcs_path")
            calculators = load_riskcalcs(path); resource = "riskcalcs"
        else: resource = "fixture"
        if mode not in {"bm25", "medcpt"}: raise ValueError(f"unknown retrieval mode: {mode}")
        if mode == "medcpt":
            raise RuntimeError("MedCPT retrieval requires optional model resources and is not installed")
        self.trajectory.append({"event": "calculator_search", "mode": mode, "resource": resource})
        query = self.client.complete("calculator_query", {"question": item["instruction"]})
        scored = bm25_rank(" ".join(query.get("terms", [])), calculators, int(self.config.get("top_k", 10)))
        selected = self.client.complete("select_calculator", {"question": item["instruction"], "candidates": scored})
        calculator = next((c for c in calculators if c["id"] == selected["calculator_id"]), None)
        if calculator is None: raise ValueError("selected unknown calculator")
        self.trajectory.append({"event": "calculator_selected", "calculator_id": calculator["id"]})
        values = self.client.complete("extract_inputs", {"question": item["instruction"], "calculator": calculator})
        if calculator.get("kind") == "bmi":
            result = values["weight_kg"] / math.pow(values["height_m"], 2)
        else:
            raise RuntimeError(f"calculator implementation unavailable: {calculator.get('kind')}")
        self.trajectory.append({"event": "calculator_run", "inputs": values, "result": result})
        final = self.client.complete("calculator_answer", {"calculator": calculator, "inputs": values, "result": result})
        return {"final_answer": final, "trajectory": self.trajectory,
                "usage": {"model_calls": len(self.client.calls), "tool_calls": 3},
                "artifacts": {"calculator_result.json": {"calculator": calculator, "inputs": values, "result": result,
                                                          "retrieval_mode": mode, "resource_scope": resource}}}
