"""Tests for validation helpers."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from validators import (
    Summary,
    check_no_nans,
    check_prices_positive,
    summary_report,
    close_histogram,
    volume_magnitude_histogram,
    zero_activity_by_asset,
)


def test_check_prices_positive_passes() -> None:
    df = pd.DataFrame({"close": [1.0, 2.5, 3.1]})
    assert check_prices_positive(df)


def test_check_prices_positive_fails() -> None:
    df = pd.DataFrame({"close": [1.0, -0.1]})
    assert not check_prices_positive(df)


def test_check_prices_positive_missing_column() -> None:
    df = pd.DataFrame({"price": [1.0]})
    with pytest.raises(KeyError):
        check_prices_positive(df)


def test_check_no_nans_true() -> None:
    df = pd.DataFrame({"date": ["2024-01-01"], "asset": ["PETR4"], "close": [1.0]})
    assert check_no_nans(df, ["date", "asset"])


def test_check_no_nans_false() -> None:
    df = pd.DataFrame({"date": ["2024-01-01", None], "asset": ["PETR4", "VALE3"]})
    assert check_no_nans(df, ["date", "asset"]) is False


def test_check_no_nans_missing_column() -> None:
    df = pd.DataFrame({"date": ["2024-01-01"]})
    with pytest.raises(KeyError):
        check_no_nans(df, ["asset"])


def test_summary_report_handles_dates() -> None:
    df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-05"],
            "asset": ["PETR4", "VALE3"],
            "close": [1.0, 2.0],
        }
    )
    summary = summary_report(df)

    assert summary == Summary(rows=2, assets=2, date_min="2024-01-01", date_max="2024-01-05")


def test_summary_report_empty_dataset() -> None:
    df = pd.DataFrame({"date": [], "asset": []})
    summary = summary_report(df)

    assert summary == Summary(rows=0, assets=0, date_min=None, date_max=None)

def test_zero_activity_prefers_totneg() -> None:
    df = pd.DataFrame({
        'asset': ['PETR4', 'PETR4', 'VALE3'],
        'TOTNEG': [0, 5, 0],
        'volume': [100, 200, 0],
    })

    result = zero_activity_by_asset(df)

    assert result.to_dict() == {'PETR4': 1, 'VALE3': 1}


def test_zero_activity_fallback_volume() -> None:
    df = pd.DataFrame({
        'asset': ['PETR4', 'VALE3', 'VALE3'],
        'volume': [0, 0, 10],
    })

    result = zero_activity_by_asset(df)

    assert result.to_dict() == {'PETR4': 1, 'VALE3': 1}


def test_close_histogram_returns_bins() -> None:
    df = pd.DataFrame({'close': [1, 2, 3, 4, 5]})

    hist = close_histogram(df, bins=2)

    assert len(hist) == 2
    assert sum(count for _, count in hist) == 5


def test_volume_magnitude_histogram_orders() -> None:
    df = pd.DataFrame({'volume': [0, 1, 10, 500, 1200]})

    hist = dict(volume_magnitude_histogram(df))

    expected = {'<=0': 1, '1e0': 1, '1e1': 1, '1e2': 1, '1e3': 1}
    assert hist == expected

