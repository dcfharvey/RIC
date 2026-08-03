"""Point d'entrée minimal du vivarium (python -m vivarium)."""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
