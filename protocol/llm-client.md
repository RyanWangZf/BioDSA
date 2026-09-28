# Optional LLM client boundary

Agents may use a shared client, but it is not part of agent conformance.
`harness.llm` defines plain dataclasses with no framework types.

`LLMRequest` contains `model`, ordered `{role, content}` messages, optional JSON
Schema tool definitions, generation parameters, and provider-specific options.
Model names are opaque strings. `LLMResponse` contains content, tool calls,
finish reason, and optional usage; missing usage is unknown.

`complete(request, timeout_seconds=...)` has a caller-visible deadline. Client
implementations may retry transient rate-limit, unavailable, and transport
errors up to their configured retry policy and deadline. Authentication,
invalid-request, and context-limit errors are permanent. Exhaustion raises
`LLMClientError` with a stable `code`, `retryable` flag, and sanitized message.
Clients must not silently retry after the total timeout or expose credentials in
errors. `FakeClient` returns queued deterministic responses for tests.
