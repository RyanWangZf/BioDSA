"""HTTP clients for verifier-owned DeepRare gateways."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


def _post(base: str, token: str, path: str, payload: dict, timeout: int) -> dict:
    request = urllib.request.Request(
        base.rstrip("/") + path,
        data=json.dumps(payload).encode(),
        method="POST", headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(2 * 1024 * 1024)
    except urllib.error.HTTPError as exc:
        raw = exc.read(1024 * 1024)
        try: value = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError): value = {"error": f"gateway_http_{exc.code}"}
        return value if isinstance(value, dict) else {"error": f"gateway_http_{exc.code}"}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("gateway response must be an object")
    return value


def query_model(messages: list[dict], config: dict) -> str:
    response = _post(config.get("model_gateway_url") or os.environ["RDD_MODEL_GATEWAY_URL"],
                     os.environ[config.get("model_gateway_token_env", "RDD_MODEL_GATEWAY_TOKEN")],
                     "/v1/model", {"messages": messages,
                                    "max_output_tokens": int(config.get("max_output_tokens", 6144))},
                     int(config.get("model_gateway_timeout_seconds", os.getenv("RDD_MODEL_GATEWAY_TIMEOUT_SECONDS", "300"))))
    text=response.get("text")
    if not isinstance(text,str): raise RuntimeError(str(response.get("error","model gateway omitted text")))
    return text


def query_source(tool: str, arguments: dict, config: dict) -> dict:
    return _post(config.get("source_gateway_url") or os.environ["RDD_SOURCE_GATEWAY_URL"],
                 os.environ[config.get("source_gateway_token_env", "RDD_SOURCE_GATEWAY_TOKEN")],
                 "/v1/source", {"tool": tool, "arguments": arguments}, 70)
