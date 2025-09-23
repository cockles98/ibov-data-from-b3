"""Parsers for Ibovespa portfolio (carteira) files."""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd

from logging_utils import get_console

__all__ = ["load_carteira_csv", "load_all_carteiras"]

_FILE_PATTERN = re.compile(r"IBOV_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.csv$", re.IGNORECASE)
console = get_console()


def _normalize_label(label: str) -> str:
    """Return ``label`` lowercased, unaccented and stripped of spaces."""
    normalized = unicodedata.normalize("NFKD", label)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return without_accents.lower().replace(" ", "")


def _normalize_asset(series: pd.Series) -> pd.Series:
    """Return asset codes stripped, uppercased and without internal spaces."""
    return series.astype(str).str.strip().str.upper().str.replace(" ", "", regex=False)


def _ensure_asset_column(df: pd.DataFrame) -> str:
    for column in df.columns:
        if _normalize_label(column) == "codigo":
            return column
    raise ValueError("Coluna de codigo nao encontrada no arquivo de carteira")


def load_carteira_csv(path: str | Path, start: date, end: date) -> pd.DataFrame:
    """Load a single carteira CSV file, normalizing asset identifiers."""

    if start > end:
        raise ValueError(
            f"Data inicial {start.isoformat()} posterior a data final {end.isoformat()}"
        )

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo de carteira nao encontrado: {file_path}")

    console.log(f"[bold cyan]Carregando carteira[/]: {file_path}")

    try:
        df = pd.read_csv(file_path, sep=None, engine="python")
    except Exception as exc:  # pragma: no cover - pandas raises multiple subclasses
        raise ValueError(f"Falha ao ler {file_path}: {exc}") from exc

    asset_col = _ensure_asset_column(df)

    result = df.copy()
    result["asset"] = _normalize_asset(result[asset_col])
    result["start"] = pd.to_datetime(start)
    result["end"] = pd.to_datetime(end)

    console.log(f"Carteira {file_path.name}: {len(result)} linhas carregadas.")
    if result.empty:
        console.log(f"[yellow]Aviso: carteira {file_path.name} nao possui linhas.[/]")

    column_order = ["asset", "start", "end"] + [col for col in result.columns if col not in {"asset", "start", "end"}]
    return result[column_order]


def load_all_carteiras(directory: str | Path = Path("data") / "ibov_carteiras") -> pd.DataFrame:
    """Load all carteira CSV files located in ``directory``."""

    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Diretorio de carteiras nao encontrado: {dir_path}")

    console.log(f"[bold cyan]Carregando carteiras do diretorio[/]: {dir_path}")

    frames: list[pd.DataFrame] = []
    for file_path in sorted(dir_path.glob("IBOV_*.csv")):
        match = _FILE_PATTERN.match(file_path.name)
        if not match:
            console.log(f"[yellow]Ignorando arquivo sem padrao IBOV: {file_path.name}[/]")
            continue
        start_str, end_str = match.groups()
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
        frame = load_carteira_csv(file_path, start=start_date, end=end_date)
        frames.append(frame)

    if not frames:
        console.log(f"[yellow]Aviso: nenhum arquivo de carteira valido em {dir_path}.[/]")
        return pd.DataFrame(columns=["asset", "start", "end"])

    combined = pd.concat(frames, ignore_index=True)
    console.log(f"Total de linhas em carteiras: {len(combined)}")
    return combined
