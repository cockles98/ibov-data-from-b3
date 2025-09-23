"""Tests for joining quotes with Ibovespa ranges."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from join_universe import join_quotes_with_ibov_ranges


def test_join_quotes_with_ibov_ranges_matches_boundaries() -> None:
    quotes = pd.DataFrame(
        {
            "asset": ["PETR4", "PETR4", "PETR4"],
            "date_raw": ["20240101", "20240131", "20240201"],
            "close": [10.0, 11.0, 12.0],
        }
    )
    ranges = pd.DataFrame(
        {
            "asset": ["PETR4", "VALE3"],
            "start": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-10")],
            "end": [pd.Timestamp("2024-01-31"), pd.Timestamp("2024-02-29")],
        }
    )

    result = join_quotes_with_ibov_ranges(quotes, ranges)

    assert result.shape[0] == 2
    assert result["date"].tolist() == [date(2024, 1, 1), date(2024, 1, 31)]


def test_join_quotes_with_ibov_ranges_requires_columns() -> None:
    quotes = pd.DataFrame({"date_raw": ["20240101"]})
    ranges = pd.DataFrame({"asset": ["PETR4"], "start": ["2024-01-01"], "end": ["2024-01-31"]})

    with pytest.raises(KeyError):
        join_quotes_with_ibov_ranges(quotes, ranges)



def test_join_quotes_with_ibov_ranges_invalid_date() -> None:
    quotes = pd.DataFrame({"asset": ["PETR4"], "date_raw": ["2024-13-01"]})
    ranges = pd.DataFrame({"asset": ["PETR4"], "start": ["2024-01-01"], "end": ["2024-01-31"]})

    with pytest.raises(ValueError):
        join_quotes_with_ibov_ranges(quotes, ranges)
