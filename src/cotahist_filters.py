"""Filtering utilities for COTAHIST data."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from logging_utils import get_console

__all__ = ["filter_equities"]

console = get_console()


def _normalize_asset(asset_series: pd.Series) -> pd.Series:
    """Return ``asset_series`` stripped of whitespace and upper-cased."""
    return asset_series.astype(str).str.strip().str.upper().str.replace(" ", "", regex=False)


def filter_equities(df: pd.DataFrame) -> pd.DataFrame:
    """Filter COTAHIST records keeping only regular equities (BDI ``02``).

    The function also removes:
    - BDI ``96`` (assets suspended from trading)
    - instruments whose ``spec`` field is exactly ``BDR``

    The ``asset`` column is normalized (strip, upper, remove spaces) before
    returning the filtered DataFrame.
    """

    if "BDI" not in df.columns or "asset" not in df.columns:
        raise KeyError("Input DataFrame must include 'BDI' and 'asset' columns")

    filtered = df.copy()
    filtered["asset"] = _normalize_asset(filtered["asset"])

    mask_bdi_valid = filtered["BDI"].astype(str).str.strip() == "02"
    mask_bdi_excluded = filtered["BDI"].astype(str).str.strip() == "96"
    mask_spec_bdr = filtered.get("spec", pd.Series(index=filtered.index, dtype="object")).astype(str).str.strip().eq("BDR")

    result = filtered[mask_bdi_valid & ~mask_bdi_excluded & ~mask_spec_bdr]
    if result.empty:
        console.log("[yellow]Aviso: nenhum ativo restante apos filtro de mercado a vista.[/]")
    return result.reset_index(drop=True)

