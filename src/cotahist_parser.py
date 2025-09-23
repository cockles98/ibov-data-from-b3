"""Parser helpers for COTAHIST fixed-width files."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import pandas as pd

from logging_utils import get_console

__all__ = ["parse_cotahist_file"]

console = get_console()

_RECORD_TYPE_SLICE = slice(0, 2)
_DATE_SLICE = slice(2, 10)
_BDI_SLICE = slice(10, 12)
_ASSET_SLICE = slice(12, 24)
_SPEC_SLICE = slice(39, 49)
_CLOSE_SLICE = slice(108, 121)
_VOLUME_SHARES_SLICE = slice(152, 170)
_VOLUME_BRL_SLICE = slice(170, 188)

MIN_LENGTH = max(
    _DATE_SLICE.stop,
    _BDI_SLICE.stop,
    _ASSET_SLICE.stop,
    _SPEC_SLICE.stop,
    _CLOSE_SLICE.stop,
    _VOLUME_SHARES_SLICE.stop,
    _VOLUME_BRL_SLICE.stop,
)


def _parse_int(raw: str) -> int:
    """Return ``raw`` converted to integer, accepting blank values as zero."""
    value = raw.strip()
    return int(value) if value else 0


def _parse_price(raw: str) -> float:
    """Return a monetary value encoded in cents as a float."""
    return _parse_int(raw) / 100


def _parse_line(line: str, *, line_number: int, source: Path) -> dict[str, object] | None:
    """Parse a single COTAHIST record line if it is of type ``01``."""
    if len(line) < MIN_LENGTH:
        raise ValueError(
            f"linha com tamanho {len(line)} inferior ao esperado ({MIN_LENGTH})"
        )
    if line[_RECORD_TYPE_SLICE] != "01":
        return None

    return {
        "date_raw": line[_DATE_SLICE].strip(),
        "BDI": line[_BDI_SLICE].strip(),
        "asset": line[_ASSET_SLICE].strip(),
        "spec": line[_SPEC_SLICE].strip(),
        "close": _parse_price(line[_CLOSE_SLICE]),
        "volume_shares": _parse_int(line[_VOLUME_SHARES_SLICE]),
        "volume_brl": _parse_price(line[_VOLUME_BRL_SLICE]),
    }


def parse_cotahist_file(path: str | Path) -> pd.DataFrame:
    """Parse a COTAHIST file and return a DataFrame with key trading columns."""

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo COTAHIST nao encontrado: {file_path}")

    console.log(f"[bold cyan]Iniciando leitura do COTAHIST[/]: {file_path}")
    records: List[dict[str, object]] = []
    total_lines = 0

    try:
        with file_path.open("r", encoding="latin-1") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                total_lines += 1
                line = raw_line.rstrip("\r\n")
                try:
                    parsed = _parse_line(line, line_number=line_number, source=file_path)
                except ValueError as exc:
                    raise ValueError(
                        f"Erro ao interpretar linha {line_number} em {file_path.name}: {exc}"
                    ) from exc
                if parsed is not None:
                    records.append(parsed)
    except UnicodeDecodeError as exc:
        raise ValueError(f"Falha ao decodificar {file_path}: {exc}") from exc

    console.log(
        f"Arquivo {file_path.name}: {len(records)} registros tipo '01' a partir de {total_lines} linhas."
    )
    if not records:
        console.log(f"[yellow]Aviso: nenhuma negociacao encontrada em {file_path}.[/]")

    columns = [
        "date_raw",
        "BDI",
        "asset",
        "spec",
        "close",
        "volume_shares",
        "volume_brl",
    ]
    return pd.DataFrame(records, columns=columns)
