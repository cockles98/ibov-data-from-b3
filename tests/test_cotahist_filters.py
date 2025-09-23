"""Tests for COTAHIST filtering utilities."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from cotahist_filters import filter_equities


def test_filter_equities_keeps_regular_assets() -> None:
    df = pd.DataFrame(
        {
            "BDI": ["02", "02", "96", "02"],
            "asset": [" petr4 ", "VALE3", "PETR4", " XPTO11 "],
            "spec": ["PN    N1", "BDR", "PN    N1", "ON     NM"],
        }
    )

    result = filter_equities(df)

    assert list(result["asset"]) == ["PETR4", "XPTO11"]
    assert result.shape[0] == 2


def test_filter_equities_requires_columns() -> None:
    df = pd.DataFrame({"asset": ["PETR4"]})

    with pytest.raises(KeyError):
        filter_equities(df)
