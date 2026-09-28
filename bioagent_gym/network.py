from __future__ import annotations

from typing import Any

from .errors import HarnessError


DEFAULT_MODE = "internet"


def resolve_network(agent: dict[str, Any], benchmark: dict[str, Any], execution: dict[str, Any]) -> dict[str, Any]:
    manifest = agent.get("network", {})
    override = execution.get("network", {})
    has_sandbox = "sandbox" in agent
    resolved: dict[str, Any] = {}
    for layer in ("agent", "sandbox"):
        mode, source = DEFAULT_MODE, "framework_default"
        if layer in manifest:
            mode, source = manifest[layer]["mode"], "agent_manifest"
        if layer in override:
            mode, source = override[layer]["mode"], "experiment"
        applicable = layer == "agent" or has_sandbox
        resolved[layer] = {"mode": mode if applicable else None, "source": source if applicable else "not_applicable", "applicable": applicable}

    constraints = benchmark.get("network_constraints", {})
    for layer, rule in constraints.items():
        current = resolved[layer]
        if not current["applicable"]:
            continue
        if current["mode"] not in rule["allowed_modes"]:
            allowed = ", ".join(rule["allowed_modes"])
            raise HarnessError(f"network policy conflict: benchmark allows {layer} modes [{allowed}], resolved mode is {current['mode']!r}")

    backend = execution["backend"]
    requested_none = [name for name, item in resolved.items() if item["applicable"] and item["mode"] == "none"]
    if backend == "local" and requested_none:
        raise HarnessError(f"local backend cannot enforce network mode 'none' for {', '.join(requested_none)}; use the docker backend")
    separate = has_sandbox and resolved["agent"]["mode"] != resolved["sandbox"]["mode"]
    if separate and backend != "docker":
        raise HarnessError("different agent and sandbox network modes require the docker backend")
    if separate and not agent.get("sandbox", {}).get("docker"):
        raise HarnessError("different agent and sandbox network modes require sandbox.docker configuration")

    for item in resolved.values():
        if not item["applicable"]:
            item.update({"enforced": False, "enforcement": "not_applicable"})
        elif backend == "docker":
            item.update({"enforced": True, "enforcement": "docker_network_mode"})
        else:
            item.update({"enforced": False, "enforcement": "host_network_available"})
    resolved.update({
        "backend": backend,
        "boundary": "separate" if separate else ("shared" if has_sandbox else "agent_only"),
    })
    return resolved
