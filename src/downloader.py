"""Utilities for downloading COTAHIST and Ibovespa carteira datasets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Iterable, List, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from logging_utils import get_console
from utils_io import ensure_dirs

console = get_console()

DEFAULT_COTAHIST_TEMPLATE = "https://example.com/b3/cotahist/COTAHIST_{year}.zip"
DEFAULT_TIMEOUT = 60  # seconds


class DownloadError(RuntimeError):
    """Raised when a download attempt fails."""


def _default_fetch(url: str, *, timeout: int = DEFAULT_TIMEOUT) -> bytes:
    """Fetch ``url`` returning raw bytes, raising ``DownloadError`` on failure."""

    try:
        with urlopen(url, timeout=timeout) as response:  # type: ignore[arg-type]
            status = getattr(response, "status", response.getcode())
            if status and status >= 400:
                raise DownloadError(f"HTTP {status} ao baixar {url}")
            return response.read()
    except (HTTPError, URLError, TimeoutError) as exc:  # pragma: no cover - network errors
        raise DownloadError(f"Falha ao baixar {url}: {exc}") from exc


@dataclass(frozen=True)
class CarteiraDownloadSpec:
    """Describe a carteira download entry."""

    url: str
    start: date
    end: date
    filename: str | None = None

    def output_name(self) -> str:
        if self.filename:
            return self.filename
        return f"IBOV_{self.start.isoformat()}_{self.end.isoformat()}.csv"


def download_cotahist_years(
    years: Sequence[int],
    *,
    base_template: str = DEFAULT_COTAHIST_TEMPLATE,
    destination: Path | str = Path("data") / "cotahist",
    overwrite: bool = False,
    fetcher: Callable[[str], bytes] = _default_fetch,
) -> List[Path]:
    """Download COTAHIST files for the given ``years``.

    ``base_template`` should contain ``{year}`` placeholder to format the URL.
    """

    if "{year}" not in base_template:
        raise ValueError("base_template deve conter o placeholder '{year}'")

    dest_path = Path(destination)
    ensure_dirs()
    dest_path.mkdir(parents=True, exist_ok=True)

    downloaded: List[Path] = []
    for year in years:
        url = base_template.format(year=year)
        file_name = Path(url).name or f"COTAHIST_{year}.zip"
        target = dest_path / file_name
        if target.exists() and not overwrite:
            console.log(f"[yellow]Arquivo ja existe, pulando[/]: {target}")
            downloaded.append(target)
            continue

        console.log(f"[bold]Baixando COTAHIST[/]: {year} -> {url}")
        data = fetcher(url)
        target.write_bytes(data)
        console.log(f"Arquivo salvo em {target} ({len(data)} bytes)")
        downloaded.append(target)

    return downloaded


def download_carteiras(
    entries: Iterable[CarteiraDownloadSpec],
    *,
    destination: Path | str = Path("data") / "ibov_carteiras",
    overwrite: bool = False,
    fetcher: Callable[[str], bytes] = _default_fetch,
) -> List[Path]:
    """Download carteira files according to ``entries`` specification."""

    dest_path = Path(destination)
    ensure_dirs()
    dest_path.mkdir(parents=True, exist_ok=True)

    downloaded: List[Path] = []
    for spec in entries:
        file_name = spec.output_name()
        target = dest_path / file_name
        if target.exists() and not overwrite:
            console.log(f"[yellow]Arquivo ja existe, pulando[/]: {target}")
            downloaded.append(target)
            continue

        console.log(
            f"[bold]Baixando carteira[/]: {spec.start.isoformat()} -> {spec.end.isoformat()} ({spec.url})"
        )
        data = fetcher(spec.url)
        target.write_bytes(data)
        console.log(f"Carteira salva em {target} ({len(data)} bytes)")
        downloaded.append(target)

    return downloaded



