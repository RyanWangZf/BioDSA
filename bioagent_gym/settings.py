from __future__ import annotations

import os
from pathlib import Path


ENV_PREFIX = "BIOAGENT_GYM_"


def cache_dir() -> Path:
    """Return the configured cache root without creating or moving anything."""
    configured = os.environ.get(f"{ENV_PREFIX}CACHE_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".cache" / "bioagent-gym"
