"""Tests for utility filesystem helpers."""

from pathlib import Path
import sys

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils_io import ensure_dirs, list_carteiras_files, list_cotahist_files


def test_ensure_dirs_creates_expected_structure(tmp_path: Path) -> None:
    ensure_dirs(tmp_path)

    assert (tmp_path / "data" / "cotahist").is_dir()
    assert (tmp_path / "data" / "ibov_carteiras").is_dir()
    assert (tmp_path / "out").is_dir()


def test_list_cotahist_files_filters_and_sorts(tmp_path: Path) -> None:
    cotahist_dir = tmp_path / "cotahist"
    cotahist_dir.mkdir()

    expected_files = [
        cotahist_dir / "COTAHIST.A2023.TXT",
        cotahist_dir / "COTAHIST.B2022.TXT",
        cotahist_dir / "COTAHIST_A2024.TXT",
    ]
    for file_path in expected_files:
        file_path.write_text("dummy")

    (cotahist_dir / "README.txt").write_text("ignored")

    result = list_cotahist_files(cotahist_dir)

    assert result == sorted(expected_files, key=lambda item: item.name)


def test_list_cotahist_files_handles_missing_directory(tmp_path: Path) -> None:
    missing_dir = tmp_path / "does_not_exist"

    result = list_cotahist_files(missing_dir)

    assert result == []


def test_list_carteiras_files_returns_sorted_files(tmp_path: Path) -> None:
    carteiras_dir = tmp_path / "ibov_carteiras"
    carteiras_dir.mkdir()

    file_a = carteiras_dir / "2023-01.xlsx"
    file_b = carteiras_dir / "2022-12.xlsx"
    file_a.write_text("a")
    file_b.write_text("b")
    (carteiras_dir / "subdir").mkdir()

    result = list_carteiras_files(carteiras_dir)

    assert result == [file_b, file_a]
