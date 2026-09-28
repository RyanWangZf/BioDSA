"""Deprecated compatibility namespace for the phase-1 BioAgent Gym harness."""
from __future__ import annotations

import warnings

warnings.warn(
    "The 'harness' package is deprecated; import 'bioagent_gym' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from bioagent_gym import __version__

__all__ = ["__version__"]
