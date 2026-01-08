"""Environment helpers.

We support loading configuration from a `.env` file at repo root.
This keeps secrets like `GEMINI_API_KEY` out of source control.

All code should still work if python-dotenv is not installed; in that case
we simply don't auto-load `.env`.
"""

from __future__ import annotations

from pathlib import Path


def load_repo_dotenv(*, override: bool = False) -> bool:
    """Load `.env` from repo root if present.

    Returns:
        True if `.env` was found and load was attempted, else False.
    """

    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    if not env_path.exists():
        return False

    try:
        from dotenv import load_dotenv
    except Exception:
        return False

    load_dotenv(dotenv_path=env_path, override=bool(override))
    return True
