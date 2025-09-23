"""Tests for downloader utilities and CLI integration."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
from typing import List

import pytest

typer_module = pytest.importorskip("typer")
from typer.testing import CliRunner

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import cli
from downloader import (
    CarteiraDownloadSpec,
    download_carteiras,
    download_cotahist_years,
)

runner = CliRunner()


def test_download_cotahist_years_writes_files(tmp_path: Path) -> None:
    requests: List[str] = []

    def fake_fetch(url: str) -> bytes:
        requests.append(url)
        return b"cotahist"

    output = download_cotahist_years(
        [2024, 2025],
        base_template="https://example.test/COTAHIST_{year}.zip",
        destination=tmp_path,
        fetcher=fake_fetch,
    )

    assert requests == [
        "https://example.test/COTAHIST_2024.zip",
        "https://example.test/COTAHIST_2025.zip",
    ]
    assert [path.exists() for path in output] == [True, True]
    assert (tmp_path / "COTAHIST_2024.zip").read_bytes() == b"cotahist"


def test_download_carteiras_saves_files(tmp_path: Path) -> None:
    payload = b"codigo,peso\nPETR4,10\n"

    def fake_fetch(url: str) -> bytes:
        return payload

    specs = [
        CarteiraDownloadSpec(
            url="https://example.test/carteira.csv",
            start=date(2025, 9, 2),
            end=date(2026, 1, 2),
        ),
    ]
    output = download_carteiras(specs, destination=tmp_path, fetcher=fake_fetch)

    expected = tmp_path / "IBOV_2025-09-02_2026-01-02.csv"
    assert output == [expected]
    assert expected.read_bytes() == payload


def test_cli_download_cotahist_invokes_utility(monkeypatch, tmp_path: Path) -> None:
    called = {}

    def fake_download(years, **kwargs):
        called["years"] = list(years)
        called.update(kwargs)
        return []

    monkeypatch.setattr(cli, "download_cotahist_years", fake_download)

    result = runner.invoke(
        cli.app,
        [
            "download",
            "cotahist",
            "2020",
            "2021",
            "--base-url-template",
            "https://example/{year}.zip",
            "--destination",
            str(tmp_path),
            "--overwrite",
        ],
    )

    assert result.exit_code == 0
    assert called["years"] == [2020, 2021]
    assert called["base_template"] == "https://example/{year}.zip"
    assert called["destination"] == tmp_path
    assert called["overwrite"] is True


def test_cli_download_carteiras_invokes_utility(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    def fake_download(specs, **kwargs):
        captured["specs"] = specs
        captured.update(kwargs)
        return []

    monkeypatch.setattr(cli, "download_carteiras", fake_download)

    result = runner.invoke(
        cli.app,
        [
            "download",
            "carteiras",
            "--urls",
            "https://example/a.csv,2025-09-02,2026-01-02",
            "--urls",
            "https://example/b.csv,2026-01-03,2026-04-01,custom.csv",
            "--destination",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert len(captured["specs"]) == 2
    first = captured["specs"][0]
    assert first.url == "https://example/a.csv"
    assert first.output_name() == "IBOV_2025-09-02_2026-01-02.csv"
    second = captured["specs"][1]
    assert second.output_name() == "custom.csv"
    assert captured["destination"] == tmp_path
    assert captured["overwrite"] is False
