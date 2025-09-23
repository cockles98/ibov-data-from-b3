"""Tests for the raw COTAHIST parser."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from cotahist_parser import parse_cotahist_file

FIXTURES_DIR = Path(__file__).parent / "fixtures"

_RECORD_TYPE_SLICE = slice(0, 2)
_DATE_SLICE = slice(2, 10)
_BDI_SLICE = slice(10, 12)
_ASSET_SLICE = slice(12, 24)
_SPEC_SLICE = slice(39, 49)
_CLOSE_SLICE = slice(108, 121)
_VOLUME_SHARES_SLICE = slice(152, 170)
_VOLUME_BRL_SLICE = slice(170, 188)


def _build_cotahist_line(
    *,
    record_type: str = "01",
    date: str = "20240102",
    bdi: str = "02",
    asset: str = "PETR4",
    spec: str = "PN    N1",
    close_cents: int = 1234567,
    volume_shares: int = 987654,
    volume_brl_cents: int = 7654321,
) -> str:
    line_length = 245
    line = [" "] * line_length

    def fill(slice_: slice, value: str, *, pad: str = " ", align: str = "left") -> None:
        width = slice_.stop - slice_.start
        text = value
        if align == "left":
            text = text.ljust(width)
        else:
            text = text.rjust(width, pad)
        line[slice_.start : slice_.stop] = list(text[:width])

    fill(_RECORD_TYPE_SLICE, record_type)
    fill(_DATE_SLICE, date)
    fill(_BDI_SLICE, bdi)
    fill(_ASSET_SLICE, asset)
    fill(_SPEC_SLICE, spec)
    fill(_CLOSE_SLICE, f"{close_cents:013d}", pad="0", align="right")
    fill(_VOLUME_SHARES_SLICE, f"{volume_shares:018d}", pad="0", align="right")
    fill(_VOLUME_BRL_SLICE, f"{volume_brl_cents:018d}", pad="0", align="right")

    return "".join(line) + "\n"


def test_parse_cotahist_fixture_file() -> None:
    df = parse_cotahist_file(FIXTURES_DIR / "cotahist_sample.txt")

    assert len(df) == 7
    assert {"02", "96"}.issubset(set(df["BDI"]))
    assert "PETR4" in df["asset"].tolist()
    assert pytest.approx(df.loc[df["asset"] == "PETR4", "close"].iloc[0], rel=1e-6) == 12345.0


def test_parse_cotahist_file_returns_expected_dataframe(tmp_path: Path) -> None:
    file_path = tmp_path / "COTAHIST_TEST.TXT"
    line = _build_cotahist_line(
        date="20240102",
        bdi="02",
        asset="PETR4",
        spec="PN      N1",
        close_cents=1234567,
        volume_shares=987654,
        volume_brl_cents=7654321,
    )
    line_ignored = _build_cotahist_line(record_type="99")
    file_path.write_text(line + line_ignored, encoding="latin-1")

    df = parse_cotahist_file(file_path)

    assert list(df.columns) == [
        "date_raw",
        "BDI",
        "asset",
        "spec",
        "close",
        "volume_shares",
        "volume_brl",
    ]
    assert len(df) == 1
    row = df.iloc[0]
    assert row["date_raw"] == "20240102"
    assert row["BDI"] == "02"
    assert row["asset"] == "PETR4"
    assert row["spec"] == "PN      N1".strip()
    assert row["close"] == pytest.approx(12345.67)
    assert row["volume_shares"] == 987654
    assert row["volume_brl"] == pytest.approx(76543.21)


def test_parse_cotahist_file_handles_absence_of_records(tmp_path: Path) -> None:
    file_path = tmp_path / "COTAHIST_TEST_EMPTY.TXT"
    file_path.write_text(_build_cotahist_line(record_type="99"), encoding="latin-1")

    df = parse_cotahist_file(file_path)

    assert df.empty
    assert list(df.columns) == [
        "date_raw",
        "BDI",
        "asset",
        "spec",
        "close",
        "volume_shares",
        "volume_brl",
    ]
