from __future__ import annotations

from app.config import load_settings
from app.runtime import run_bot


def main() -> None:
    settings = load_settings()
    run_bot(settings)


if __name__ == "__main__":
    main()
