"""Compatibility wrapper for the phase-1 module path."""
import warnings

from bioagent_gym.cli import *  # noqa: F403
from bioagent_gym.cli import main


if __name__ == "__main__":
    warnings.warn(
        "python -m harness.cli is deprecated; use python -m bioagent_gym.",
        DeprecationWarning,
        stacklevel=1,
    )
    raise SystemExit(main())
