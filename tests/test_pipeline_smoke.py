"""Smoke tests for the full pipeline."""

from __future__ import annotations

from pathlib import Path
import shutil
import sys

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pipeline import build_ibov_csv

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_pipeline_smoke(tmp_path: Path) -> None:
    cotahist_dir = tmp_path / "data" / "cotahist"
    carteiras_dir = tmp_path / "data" / "ibov_carteiras"
    out_path = tmp_path / "out" / "ibov.csv"

    cotahist_dir.mkdir(parents=True, exist_ok=True)
    carteiras_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(FIXTURES_DIR / "cotahist_sample.txt", cotahist_dir / "COTAHIST.TEST.TXT")
    shutil.copy(
        FIXTURES_DIR / "IBOV_2025-09-02_2026-01-02.csv",
        carteiras_dir / "IBOV_2025-09-02_2026-01-02.csv",
    )

    build_ibov_csv(
        cotahist_dir=cotahist_dir,
        carteiras_dir=carteiras_dir,
        out_path=out_path,
        volume_field="volume_brl",
    )

    df = pd.read_csv(out_path)
    assert set(df.columns) == {"date", "asset", "close", "volume"}
    assert df.shape[0] == 3

