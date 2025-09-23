"""Shared logging utilities leveraging Rich when available."""

from __future__ import annotations

from typing import Final

try:  # pragma: no cover - optional dependency
    from rich.console import Console
except ModuleNotFoundError:  # pragma: no cover - fallback when Rich is missing
    class Console:  # type: ignore[override]
        """Minimal console replacement exposing ``log``."""

        def log(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            print(*args)

_console: Final = Console()


def get_console() -> Console:
    """Return a shared console instance for logging."""

    return _console
