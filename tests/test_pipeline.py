"""Tests for the main ETL pipeline."""

from __future__ import annotations

from pathlib import Path
import shutil
import sys

import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pipeline import build_ibov_csv

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _copy_fixture(src_name: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    target = destination
    shutil.copy(FIXTURES_DIR / src_name, target)
    return target


def test_build_ibov_csv_creates_expected_output(tmp_path: Path) -> None:
    cotahist_dir = tmp_path / "data" / "cotahist"
    carteiras_dir = tmp_path / "data" / "ibov_carteiras"
    out_path = tmp_path / "out" / "ibov.csv"

    _copy_fixture("cotahist_sample.txt", cotahist_dir / "COTAHIST.A2025.TXT")
    _copy_fixture("IBOV_2025-09-02_2026-01-02.csv", carteiras_dir / "IBOV_2025-09-02_2026-01-02.csv")

    result_path = build_ibov_csv(
        cotahist_dir=cotahist_dir,
        carteiras_dir=carteiras_dir,
        out_path=out_path,
    )

    assert result_path == out_path
    assert result_path.exists()

    df = pd.read_csv(result_path)
    assert df.columns.tolist() == ["date", "asset", "close", "volume"]
    assert df.shape[0] == 3
    assert df["asset"].tolist() == ["ITUB4", "PETR4", "VALE3"]
    assert df["date"].tolist() == ["2025-09-03", "2025-09-02", "2025-09-02"]
    assert df["close"].tolist() == [34567.0, 12345.0, 98765.0]
    assert df["volume"].tolist() == [6222060.0, 1851750.0, 19753000.0]


def test_build_ibov_csv_volume_shares(tmp_path: Path) -> None:
    cotahist_dir = tmp_path / "data" / "cotahist"
    carteiras_dir = tmp_path / "data" / "ibov_carteiras"
    out_path = tmp_path / "out" / "ibov.csv"

    _copy_fixture("cotahist_sample.txt", cotahist_dir / "COTAHIST.A2025.TXT")
    _copy_fixture("IBOV_2025-09-02_2026-01-02.csv", carteiras_dir / "IBOV_2025-09-02_2026-01-02.csv")

    build_ibov_csv(
        cotahist_dir=cotahist_dir,
        carteiras_dir=carteiras_dir,
        out_path=out_path,
        volume_field="volume_shares",
    )

    df = pd.read_csv(out_path)
    assert df.columns.tolist() == ["date", "asset", "close", "volume"]
    assert df["asset"].tolist() == ["ITUB4", "PETR4", "VALE3"]
    assert df["volume"].tolist() == [1800, 1500, 2000]


def test_build_ibov_csv_invalid_volume_field(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        build_ibov_csv(
            cotahist_dir=tmp_path / "data" / "cotahist",
            carteiras_dir=tmp_path / "data" / "ibov_carteiras",
            out_path=tmp_path / "out" / "ibov.csv",
            volume_field="invalid",
        )


def test_build_ibov_csv_requires_carteiras(tmp_path: Path) -> None:
    cotahist_dir = tmp_path / "data" / "cotahist"
    carteiras_dir = tmp_path / "data" / "ibov_carteiras"
    _copy_fixture("cotahist_sample.txt", cotahist_dir / "COTAHIST.A2025.TXT")
    carteiras_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError):
        build_ibov_csv(
            cotahist_dir=cotahist_dir,
            carteiras_dir=carteiras_dir,
            out_path=tmp_path / "out" / "ibov.csv",
        )
