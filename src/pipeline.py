"""Main ETL pipeline to build Ibovespa quote datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd

from cotahist_filters import filter_equities
from cotahist_parser import parse_cotahist_file
from ibov_carteiras import load_all_carteiras
from join_universe import join_quotes_with_ibov_ranges
from logging_utils import get_console
from utils_io import ensure_dirs, list_cotahist_files

__all__ = ["build_ibov_csv"]

_VALID_VOLUME_FIELDS: Final[frozenset[str]] = frozenset({"volume_brl", "volume_shares"})
console = get_console()


def _load_cotahist_frames(cotahist_dir: Path) -> pd.DataFrame:
    files = list_cotahist_files(cotahist_dir)
    if not files:
        console.log(f"[yellow]Nenhum arquivo COTAHIST encontrado em {cotahist_dir}.[/]")
        raise FileNotFoundError(f"Nenhum arquivo COTAHIST encontrado em {cotahist_dir}")

    frames: list[pd.DataFrame] = []
    for file_path in files:
        console.log(f"[blue]Processando arquivo COTAHIST[/]: {file_path.name}")
        frame = parse_cotahist_file(file_path)
        frames.append(frame)
        console.log(f"Arquivo {file_path.name} processado com {len(frame)} linhas válidas.")

    combined = pd.concat(frames, ignore_index=True)
    console.log(f"Total de linhas COTAHIST carregadas: {len(combined)}")
    return combined


def build_ibov_csv(
    cotahist_dir: str | Path = Path("data") / "cotahist",
    carteiras_dir: str | Path = Path("data") / "ibov_carteiras",
    out_path: str | Path = Path("out") / "ibov_b3.csv",
    volume_field: str = "volume_brl",
) -> Path:
    """Build the unified Ibovespa dataset and store it as a CSV file."""

    if volume_field not in _VALID_VOLUME_FIELDS:
        raise ValueError(
            f"volume_field deve ser um de {_VALID_VOLUME_FIELDS}, recebido '{volume_field}'."
        )

    console.log("[bold]Iniciando pipeline Ibovespa[/]")
    console.log(f"Campo de volume selecionado: {volume_field}")
    ensure_dirs()

    cotahist_path = Path(cotahist_dir)
    carteiras_path = Path(carteiras_dir)
    output_path = Path(out_path)

    console.log("[bold]Etapa 1/5: Carregando COTAHIST[/]")
    quotes = _load_cotahist_frames(cotahist_path)

    console.log("[bold]Etapa 2/5: Filtrando mercado a vista[/]")
    quotes = filter_equities(quotes)
    console.log(f"Linhas após filtro: {len(quotes)}")

    console.log("[bold]Etapa 3/5: Convertendo datas[/]")
    quotes = quotes.copy()
    quotes["date"] = pd.to_datetime(quotes["date_raw"], format="%Y%m%d", errors="raise").dt.date
    if quotes.empty:
        console.log("[yellow]Aviso: nao ha dados apos conversao de datas.[/]")

    console.log("[bold]Etapa 4/5: Carregando carteiras[/]")
    ranges = load_all_carteiras(carteiras_path)
    if ranges.empty:
        raise ValueError(f"Nenhuma carteira valida encontrada em '{carteiras_path}'.")
    console.log(f"Total de linhas em carteiras: {len(ranges)}")

    console.log("[bold]Etapa 5/5: Realizando junção[/]")
    joined = join_quotes_with_ibov_ranges(quotes, ranges)
    console.log(f"Linhas apos junção: {len(joined)}")
    if joined.empty:
        console.log("[yellow]Aviso: junção não produziu resultados.[/]")

    required_columns = {"date", "asset", "close", volume_field}
    missing_columns = required_columns - set(joined.columns)
    if missing_columns:
        raise KeyError(f"Colunas ausentes após a junção: {missing_columns}.")

    console.log("[bold]Preparando dataset final[/]")
    result = joined.loc[:, ["date", "asset", "close"]].copy()
    volume_series = pd.to_numeric(joined[volume_field], errors="coerce")
    if volume_field == "volume_shares":
        volume_series = volume_series.round().astype("Int64")
    result["volume"] = volume_series

    result = (
        result.sort_values(["asset", "date"])
        .reset_index(drop=True)
    )

    console.log(f"Escrevendo CSV em {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)

    console.log(f"[green]Pipeline concluído com {len(result)} linhas geradas.[/]")
    return output_path
