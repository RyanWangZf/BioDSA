from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMRequest:
    model: str
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] | None = None
    generation: dict[str, Any] = field(default_factory=dict)
    provider_options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMResponse:
    content: str | None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    finish_reason: str | None = None
    usage: dict[str, int] | None = None


class LLMClientError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class LLMClient(Protocol):
    def complete(self, request: LLMRequest, timeout_seconds: float) -> LLMResponse: ...


class FakeClient:
    def __init__(self, responses: list[LLMResponse]):
        self._responses = iter(responses)
        self.requests: list[LLMRequest] = []

    def complete(self, request: LLMRequest, timeout_seconds: float) -> LLMResponse:
        if timeout_seconds <= 0:
            raise LLMClientError("timeout", "deadline expired", retryable=True)
        self.requests.append(request)
        try:
            return next(self._responses)
        except StopIteration as exc:
            raise LLMClientError("fake_exhausted", "no fake response remains") from exc
