"""Utility helpers for filesystem interactions used by ibovespa_data."""

from pathlib import Path
from typing import Iterable, List, Union

PathLike = Union[str, Path]


def _ensure_directory(path: Path) -> None:
    """Create ``path`` if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def ensure_dirs(base_path: PathLike = Path(".")) -> None:
    """Ensure project data/output directories exist under ``base_path``.

    Parameters
    ----------
    base_path:
        Root directory where ``data/`` and ``out/`` trees should be ensured.
    """

    base = Path(base_path)
    for relative in (Path("data") / "cotahist", Path("data") / "ibov_carteiras", Path("out")):
        _ensure_directory(base / relative)


def _list_files(directory: Path, pattern: str | None = None) -> List[Path]:
    """Return a sorted list of files in ``directory`` optionally matching ``pattern``."""
    if not directory.exists():
        return []

    files: Iterable[Path]
    if pattern:
        files = directory.glob(pattern)
    else:
        files = directory.iterdir()
    return sorted([item for item in files if item.is_file()], key=lambda item: item.name)


def list_cotahist_files(path: PathLike = Path("data") / "cotahist") -> List[Path]:
    """List available COTAHIST text files sorted by name."""
    directory = Path(path)
    return _list_files(directory, pattern="COTAHIST.*.TXT")


def list_carteiras_files(path: PathLike = Path("data") / "ibov_carteiras") -> List[Path]:
    """List available Ibovespa portfolio files sorted by name."""
    directory = Path(path)
    return _list_files(directory)
