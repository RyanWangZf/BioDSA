"""
Central config for supported LLM API types and model names.

Used by BaseAgent and others for type hints and validation.
Support: OpenAI, Anthropic, Google, Azure (OpenAI-compatible).

Last updated: 2026-02-12
"""
from typing import Literal

# ---------------------------------------------------------------------------
# API types
# ---------------------------------------------------------------------------

SUPPORTED_API_TYPES = ("openai", "anthropic", "google", "azure")
SupportedApiType = Literal["openai", "anthropic", "google", "azure"]

# ---------------------------------------------------------------------------
# Model names by provider (canonical API IDs / deployment names)
# Add new models here when providers release them.
# ---------------------------------------------------------------------------

# OpenAI (https://platform.openai.com/docs/models)
OPENAI_MODELS = (
    # GPT-5 family
    "gpt-5.2",
    "gpt-5.2-codex",
    "gpt-5",
    "gpt-5-mini",
    # GPT-4.1 family
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    # GPT-4.5
    "gpt-4.5-preview",
    # GPT-4o family
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4o-2024-11-20",
    # GPT-4 family (legacy)
    "gpt-4-turbo",
    "gpt-4-turbo-preview",
    "gpt-4",
    "gpt-4-32k",
    # GPT-3.5 (legacy)
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    # Reasoning models
    "o1",
    "o1-mini",
    "o1-preview",
    "o3",
    "o3-mini",
    "o3-preview",
    "o4-mini",
)

# Anthropic (https://docs.anthropic.com/en/docs/about-claude/models)
ANTHROPIC_MODELS = (
    # Claude Opus 4.6
    "claude-opus-4-6",
    "claude-opus-4-6-20260205",
    # Claude Sonnet 4.5
    "claude-sonnet-4-5",
    "claude-sonnet-4-5-20250929",
    # Claude Haiku 4.5
    "claude-haiku-4-5",
    "claude-haiku-4-5-20251001",
    # Claude Sonnet 4 (earlier)
    "claude-sonnet-4-20250514",
    # Claude 3.5 family
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet",
    "claude-3-5-haiku-20241022",
    "claude-3-5-haiku",
    # Claude 3 family (legacy)
    "claude-3-opus-20240229",
    "claude-3-opus",
    "claude-3-sonnet-20240229",
    "claude-3-sonnet",
    "claude-3-haiku-20240307",
    "claude-3-haiku",
)

# Google (Gemini; https://ai.google.dev/gemini-api/docs/models)
GOOGLE_MODELS = (
    # Gemini 3 family
    "gemini-3-pro-preview",
    "gemini-3-flash-preview",
    "gemini-3-pro-image-preview",
    # Gemini 2.5 family
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    # Gemini 2.0 family
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    # Gemini 1.5 family (legacy)
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    # Gemini 1.0 (legacy)
    "gemini-1.0-pro",
    "gemini-pro",
)

# Azure OpenAI deployment names (often match OpenAI model names or custom)
AZURE_MODELS = (
    "gpt-5.2",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4.5-preview",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-35-turbo",
    "o1",
    "o1-mini",
    "o3",
    "o3-mini",
    "o3-preview",
    "o4-mini",
)

# ---------------------------------------------------------------------------
# Combined set and Literal type for model_name
# ---------------------------------------------------------------------------

ALL_SUPPORTED_MODELS = frozenset(
    OPENAI_MODELS + ANTHROPIC_MODELS + GOOGLE_MODELS + AZURE_MODELS
)

# Literal type for type checkers and IDEs
# (mirrors the tuples above — keep in sync when adding models)
SupportedModelName = Literal[
    # OpenAI — GPT-5
    "gpt-5.2",
    "gpt-5.2-codex",
    "gpt-5",
    "gpt-5-mini",
    # OpenAI — GPT-4.1
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    # OpenAI — GPT-4.5
    "gpt-4.5-preview",
    # OpenAI — GPT-4o
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4o-2024-11-20",
    # OpenAI — GPT-4 legacy
    "gpt-4-turbo",
    "gpt-4-turbo-preview",
    "gpt-4",
    "gpt-4-32k",
    # OpenAI — GPT-3.5 legacy
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    # OpenAI — reasoning
    "o1",
    "o1-mini",
    "o1-preview",
    "o3",
    "o3-mini",
    "o3-preview",
    "o4-mini",
    # Anthropic — Opus 4.6
    "claude-opus-4-6",
    "claude-opus-4-6-20260205",
    # Anthropic — Sonnet 4.5
    "claude-sonnet-4-5",
    "claude-sonnet-4-5-20250929",
    # Anthropic — Haiku 4.5
    "claude-haiku-4-5",
    "claude-haiku-4-5-20251001",
    # Anthropic — Sonnet 4
    "claude-sonnet-4-20250514",
    # Anthropic — 3.5
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet",
    "claude-3-5-haiku-20241022",
    "claude-3-5-haiku",
    # Anthropic — 3 legacy
    "claude-3-opus-20240229",
    "claude-3-opus",
    "claude-3-sonnet-20240229",
    "claude-3-sonnet",
    "claude-3-haiku-20240307",
    "claude-3-haiku",
    # Google — Gemini 3
    "gemini-3-pro-preview",
    "gemini-3-flash-preview",
    "gemini-3-pro-image-preview",
    # Google — Gemini 2.5
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    # Google — Gemini 2.0
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    # Google — Gemini 1.5 legacy
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    # Google — Gemini 1.0 legacy
    "gemini-1.0-pro",
    "gemini-pro",
    # Azure deployment names (extras)
    "gpt-35-turbo",
]
