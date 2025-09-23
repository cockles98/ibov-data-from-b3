"""Tests for Ibovespa carteira loaders."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import shutil
import sys

import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ibov_carteiras import load_all_carteiras, load_carteira_csv

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _write_csv(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_load_carteira_csv_normalizes_asset(tmp_path: Path) -> None:
    csv_path = tmp_path / "carteira.csv"
    _write_csv(
        csv_path,
        "Codigo;Peso\n petr4 ;10\nVALE3;5\n",
    )

    frame = load_carteira_csv(csv_path, start=date(2024, 1, 1), end=date(2024, 3, 31))

    assert frame["asset"].tolist() == ["PETR4", "VALE3"]
    assert frame["start"].iloc[0] == pd.Timestamp("2024-01-01")
    assert frame["end"].iloc[0] == pd.Timestamp("2024-03-31")


def test_load_carteira_csv_from_fixture() -> None:
    frame = load_carteira_csv(
        FIXTURES_DIR / "IBOV_2025-09-02_2026-01-02.csv",
        start=date(2025, 9, 2),
        end=date(2026, 1, 2),
    )

    assert frame["asset"].tolist() == ["PETR4", "VALE3", "ITUB4"]
    assert frame["start"].nunique() == 1
    assert frame["end"].nunique() == 1


def test_load_carteira_csv_requires_asset_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "invalid.csv"
    _write_csv(csv_path, "Nome;Peso\nEmpresa;10\n")

    with pytest.raises(ValueError):
        load_carteira_csv(csv_path, start=date(2024, 1, 1), end=date(2024, 1, 31))


def test_load_carteira_csv_start_before_end(tmp_path: Path) -> None:
    csv_path = tmp_path / "carteira.csv"
    _write_csv(csv_path, "Codigo;Peso\nPETR4;10\n")

    with pytest.raises(ValueError):
        load_carteira_csv(csv_path, start=date(2024, 2, 1), end=date(2024, 1, 31))


def test_load_all_carteiras_aggregates(tmp_path: Path) -> None:
    directory = tmp_path / "carteiras"
    directory.mkdir()

    shutil.copy(FIXTURES_DIR / "IBOV_2025-09-02_2026-01-02.csv", directory)
    _write_csv(
        directory / "IBOV_2026-01-03_2026-04-01.csv",
        "Codigo;Peso\nBBDC4;7\n",
    )
    (directory / "README.txt").write_text("ignore", encoding="utf-8")

    frame = load_all_carteiras(directory)

    assert sorted(frame["asset"].unique().tolist()) == ["BBDC4", "ITUB4", "PETR4", "VALE3"]
    assert frame["start"].min() == pd.Timestamp("2025-09-02")
    assert frame["end"].max() == pd.Timestamp("2026-04-01")


def test_load_all_carteiras_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_all_carteiras(tmp_path / "missing")


def test_load_all_carteiras_invalid_file_dates(tmp_path: Path) -> None:
    directory = tmp_path / "carteiras"
    directory.mkdir()
    invalid_file = directory / "IBOV_2024-03-01_2024-02-01.csv"
    _write_csv(invalid_file, "Codigo;Peso\nPETR4;10\n")

    with pytest.raises(ValueError):
        load_all_carteiras(directory)
