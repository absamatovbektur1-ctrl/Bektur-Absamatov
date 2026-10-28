"""Load KEY=VALUE pairs from the project's .env into os.environ (no dependencies)."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"


def load_env():
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def require(*names):
    """Return the values of the given env vars, or exit with a clear message."""
    load_env()
    missing = [n for n in names if not os.environ.get(n) or "your" in os.environ[n].lower()]
    if missing:
        raise SystemExit(
            "Не хватает ключей в .env: %s\n"
            "Скопируй .env.example в .env и впиши значения (см. docs/setup-accounts.md)."
            % ", ".join(missing))
    return [os.environ[n] for n in names]
