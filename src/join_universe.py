"""Join helpers to align COTAHIST quotes with Ibovespa ranges."""

from __future__ import annotations

from typing import Final

import pandas as pd

__all__ = ["join_quotes_with_ibov_ranges"]

QUOTE_DATE_COLUMN: Final = "date"
QUOTE_ASSET_COLUMN: Final = "asset"
RANGE_START_COLUMN: Final = "start"
RANGE_END_COLUMN: Final = "end"
RANGE_ASSET_COLUMN: Final = "asset"


def _ensure_date_column(quotes: pd.DataFrame) -> pd.Series:
    """Return a series of ``datetime.date`` values derived from quotes."""
    if QUOTE_DATE_COLUMN in quotes.columns and pd.api.types.is_datetime64_any_dtype(quotes[QUOTE_DATE_COLUMN]):
        return quotes[QUOTE_DATE_COLUMN].dt.date
    if "date_raw" not in quotes.columns:
        raise KeyError("Quotes DataFrame must include either 'date' or 'date_raw'.")
    try:
        date_series = pd.to_datetime(quotes["date_raw"], format="%Y%m%d", errors="raise")
    except ValueError as exc:
        raise ValueError("Invalid date format in 'date_raw'") from exc
    return date_series.dt.date


def join_quotes_with_ibov_ranges(quotes: pd.DataFrame, ranges: pd.DataFrame) -> pd.DataFrame:
    """Join quote data with Ibovespa ranges, keeping rows within validity windows."""

    if QUOTE_ASSET_COLUMN not in quotes.columns:
        raise KeyError("Quotes DataFrame must include an 'asset' column.")
    required_range_cols = {RANGE_ASSET_COLUMN, RANGE_START_COLUMN, RANGE_END_COLUMN}
    if not required_range_cols.issubset(ranges.columns):
        raise KeyError("Ranges DataFrame must include 'asset', 'start', and 'end' columns.")

    quotes_with_date = quotes.copy()
    quotes_with_date[QUOTE_DATE_COLUMN] = _ensure_date_column(quotes)

    ranges_normalized = ranges.copy()
    for column in (RANGE_START_COLUMN, RANGE_END_COLUMN):
        if pd.api.types.is_datetime64_any_dtype(ranges_normalized[column]):
            ranges_normalized[column] = ranges_normalized[column].dt.date
        else:
            ranges_normalized[column] = pd.to_datetime(ranges_normalized[column]).dt.date

    merged = quotes_with_date.merge(
        ranges_normalized,
        how="inner",
        on=QUOTE_ASSET_COLUMN,
        suffixes=("", "_range"),
    )

    mask = (
        (merged[QUOTE_DATE_COLUMN] >= merged[RANGE_START_COLUMN])
        & (merged[QUOTE_DATE_COLUMN] <= merged[RANGE_END_COLUMN])
    )
    return merged.loc[mask].reset_index(drop=True)
