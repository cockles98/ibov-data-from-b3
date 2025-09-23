"""Validation helpers for ibovespa_data datasets."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor, log10
from typing import Iterable, List, Tuple

import pandas as pd

__all__ = ["check_prices_positive", "check_no_nans", "summary_report", "zero_activity_by_asset", "close_histogram", "volume_magnitude_histogram"]


@dataclass(frozen=True)
class Summary:
    """Simple struct holding dataset summary metrics."""

    rows: int
    assets: int
    date_min: str | None
    date_max: str | None


def check_prices_positive(df: pd.DataFrame) -> bool:
    """Return ``True`` when column ``close`` exists and all values are strictly positive."""
    if "close" not in df.columns:
        raise KeyError("DataFrame must contain a 'close' column")
    series = pd.to_numeric(df["close"], errors="raise")
    return (series > 0).all()


def check_no_nans(df: pd.DataFrame, cols: Iterable[str]) -> bool:
    """Return ``True`` when specified ``cols`` have no missing values."""
    missing_columns = [col for col in cols if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Missing columns for NaN check: {missing_columns}")
    subset = df[list(cols)]
    return not subset.isna().any().any()


def summary_report(df: pd.DataFrame) -> Summary:
    """Return a summary containing counts and date span for the dataset."""
    if "asset" not in df.columns:
        raise KeyError("DataFrame must contain an 'asset' column")
    if "date" not in df.columns:
        raise KeyError("DataFrame must contain a 'date' column")

    rows = int(len(df))
    assets = int(df["asset"].nunique())

    if rows == 0:
        return Summary(rows=0, assets=assets, date_min=None, date_max=None)

    date_series = pd.to_datetime(df["date"], errors="coerce")
    if date_series.isna().all():
        return Summary(rows=rows, assets=assets, date_min=None, date_max=None)

    date_min = date_series.min().date().isoformat()
    date_max = date_series.max().date().isoformat()

    return Summary(rows=rows, assets=assets, date_min=date_min, date_max=date_max)


def zero_activity_by_asset(
    df: pd.DataFrame,
    *,
    totneg_field: str = "TOTNEG",
    volume_field: str = "volume",
) -> pd.Series:
    """Return counts per asset where activity indicators are zero."""
    if "asset" not in df.columns:
        raise KeyError("DataFrame must contain an 'asset' column")

    if totneg_field in df.columns:
        series = pd.to_numeric(df[totneg_field], errors="coerce")
    elif volume_field in df.columns:
        series = pd.to_numeric(df[volume_field], errors="coerce")
    else:
        raise KeyError("Neither TOTNEG nor volume columns available for zero-activity check")

    mask_zero = series.fillna(0) == 0
    counts = df.loc[mask_zero].groupby("asset").size().sort_values(ascending=False)
    return counts[counts > 0]


def close_histogram(
    df: pd.DataFrame,
    bins: int = 5,
) -> List[Tuple[str, int]]:
    """Return a textual histogram of close prices using `bins` intervals."""
    if "close" not in df.columns:
        raise KeyError("DataFrame must contain a 'close' column")

    close_series = pd.to_numeric(df["close"], errors="coerce").dropna()
    if close_series.empty:
        return []

    min_value, max_value = close_series.min(), close_series.max()
    if min_value == max_value:
        return [(f"{min_value:.2f}", len(close_series))]

    buckets = pd.cut(close_series, bins=bins, include_lowest=True)
    counts = buckets.value_counts().sort_index()
    formatted = []
    for interval, count in counts.items():
        formatted.append((str(interval), int(count)))
    return formatted


def volume_magnitude_histogram(
    df: pd.DataFrame,
    *,
    volume_field: str = "volume",
) -> List[Tuple[str, int]]:
    """Return counts grouped by order of magnitude for `volume_field`."""
    if volume_field not in df.columns:
        raise KeyError("DataFrame must contain the volume column")

    volume_series = pd.to_numeric(df[volume_field], errors="coerce")
    magnitudes = []
    for value in volume_series.dropna():
        if value <= 0:
            label = "<=0"
        else:
            order = floor(log10(value))
            label = f"1e{order}"
        magnitudes.append(label)

    if not magnitudes:
        return []

    counts = pd.Series(magnitudes).value_counts().sort_index()
    return [(bucket, int(count)) for bucket, count in counts.items()]
