"""Command-line interface for ibovespa_data project."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import List

import pandas as pd
import typer

try:
    from rich.console import Console
    from rich.table import Table
except ModuleNotFoundError:  # pragma: no cover - fallback when rich is unavailable
    Console = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]

from downloader import (
    DEFAULT_COTAHIST_TEMPLATE,
    CarteiraDownloadSpec,
    download_carteiras,
    download_cotahist_years,
)
from pipeline import build_ibov_csv
from validators import (
    check_no_nans,
    check_prices_positive,
    summary_report,
    close_histogram,
    volume_magnitude_histogram,
    zero_activity_by_asset,
)

app = typer.Typer(help="Ferramentas para processar dados do Ibovespa (B3).")
download_app = typer.Typer(help="Rotinas de download de arquivos da B3.")
app.add_typer(download_app, name="download")


@app.command()
def build(
    cotahist_dir: Path = typer.Option(Path("data") / "cotahist", help="Diretorio com arquivos COTAHIST.*.TXT"),
    carteiras_dir: Path = typer.Option(Path("data") / "ibov_carteiras", help="Diretorio com carteiras do Ibovespa"),
    out_path: Path = typer.Option(Path("out") / "ibov_b3.csv", help="Arquivo CSV de saida gerado pelo ETL"),
    volume_field: str = typer.Option("volume_brl", help="Campo de volume a exportar", case_sensitive=False),
) -> None:
    """Executa o pipeline completo e gera o arquivo consolidado."""

    volume = volume_field.lower()
    build_ibov_csv(
        cotahist_dir=cotahist_dir,
        carteiras_dir=carteiras_dir,
        out_path=out_path,
        volume_field=volume,
    )
    typer.echo(f"Arquivo gerado em {out_path}.")


@app.command()
def validate(path: Path = typer.Argument(Path("out") / "ibov_b3.csv")) -> None:
    """Roda validacoes simples sobre o CSV consolidado."""

    if not path.exists():
        raise typer.BadParameter(f"Arquivo {path} nao encontrado.")

    df = pd.read_csv(path)

    if df.empty:
        typer.echo("[warn] Arquivo vazio, nada para validar.")
        raise typer.Exit(code=0)

    try:
        summary = summary_report(df)
        prices_ok = check_prices_positive(df)
        core_ok = check_no_nans(df, ["date", "asset", "close", "volume"])
        zero_counts = zero_activity_by_asset(df)
        close_hist = close_histogram(df)
        volume_hist = volume_magnitude_histogram(df)
        top_assets = df["asset"].value_counts().head(10)
    except KeyError as exc:
        raise typer.BadParameter(str(exc)) from exc

    assets_ok = summary.assets > 0
    checks = [
        ("precos_positivos", prices_ok),
        ("sem_nulos_nucleares", core_ok),
        ("ativos_disponiveis", assets_ok),
    ]

    if Console and Table:  # pragma: no branch - formatting path
        console = Console()
        summary_table = Table(title="Resumo do dataset")
        summary_table.add_column("Metrica")
        summary_table.add_column("Valor")
        summary_table.add_row("Linhas", str(summary.rows))
        summary_table.add_row("Ativos", str(summary.assets))
        summary_table.add_row("Data minima", summary.date_min or "-")
        summary_table.add_row("Data maxima", summary.date_max or "-")

        checks_table = Table(title="Checagens")
        checks_table.add_column("Check")
        checks_table.add_column("Status")
        for label, ok in checks:
            checks_table.add_row(label, "OK" if ok else "FALHA")

        console.print(summary_table)
        console.print(checks_table)

        if not zero_counts.empty:
            zero_table = Table(title="Ativos com volume/TOTNEG zero")
            zero_table.add_column("Ativo")
            zero_table.add_column("Ocorrencias", justify="right")
            for asset, count in zero_counts.items():
                zero_table.add_row(asset, str(int(count)))
            console.print(zero_table)

        if close_hist:
            close_table = Table(title="Histograma de close")
            close_table.add_column("Faixa")
            close_table.add_column("Linhas", justify="right")
            for label, count in close_hist:
                close_table.add_row(label, str(count))
            console.print(close_table)

        if volume_hist:
            volume_table = Table(title="Histograma de volume")
            volume_table.add_column("Ordem")
            volume_table.add_column("Linhas", justify="right")
            for label, count in volume_hist:
                volume_table.add_row(label, str(count))
            console.print(volume_table)

        if not top_assets.empty:
            top_table = Table(title="Top 10 ativos por linhas")
            top_table.add_column("Ativo")
            top_table.add_column("Linhas", justify="right")
            for asset, count in top_assets.items():
                top_table.add_row(asset, str(int(count)))
            console.print(top_table)
    else:  # pragma: no cover - fallback output
        typer.echo("Resumo do dataset:")
        typer.echo(f"  Linhas: {summary.rows}")
        typer.echo(f"  Ativos: {summary.assets}")
        typer.echo(f"  Data minima: {summary.date_min or '-'}")
        typer.echo(f"  Data maxima: {summary.date_max or '-'}")
        typer.echo("Checagens:")
        for label, ok in checks:
            typer.echo(f"  {label}: {'OK' if ok else 'FALHA'}")

        if not zero_counts.empty:
            typer.echo('Ativos com volume/TOTNEG zero:')
            for asset, count in zero_counts.items():
                typer.echo(f'  {asset}: {int(count)}')

        if close_hist:
            typer.echo('Histograma de close:')
            for label, count in close_hist:
                typer.echo(f'  {label}: {count}')

        if volume_hist:
            typer.echo('Histograma de volume:')
            for label, count in volume_hist:
                typer.echo(f'  {label}: {count}')

        if not top_assets.empty:
            typer.echo('Top 10 ativos por linhas:')
            for asset, count in top_assets.items():
                typer.echo(f'  {asset}: {int(count)}')

    if not all(status for _, status in checks):
        raise typer.Exit(code=1)

    typer.echo("Validacao concluida com sucesso.")

def _parse_carteira_entry(entry: str) -> CarteiraDownloadSpec:
    parts = [part.strip() for part in entry.split(",") if part.strip()]
    if len(parts) not in (3, 4):
        raise typer.BadParameter(
            "Cada entrada deve seguir o formato URL,start,end[,arquivo.csv]"
        )
    try:
        start_dt = date.fromisoformat(parts[1])
        end_dt = date.fromisoformat(parts[2])
    except ValueError as exc:
        raise typer.BadParameter(f"Datas invalidas na entrada '{entry}'") from exc

    filename = parts[3] if len(parts) == 4 else None
    return CarteiraDownloadSpec(url=parts[0], start=start_dt, end=end_dt, filename=filename)


@download_app.command("cotahist")
def download_cotahist(
    years: List[int] = typer.Argument(..., metavar="YEAR...", help="Anos a serem baixados"),
    base_template: str = typer.Option(
        DEFAULT_COTAHIST_TEMPLATE,
        "--base-url-template",
        help="Template de URL contendo o placeholder {year}",
    ),
    destination: Path = typer.Option(Path("data") / "cotahist", help="Diretorio de destino"),
    overwrite: bool = typer.Option(False, help="Sobrescreve arquivos existentes"),
) -> None:
    """Baixa arquivos COTAHIST para os anos informados."""

    download_cotahist_years(
        years,
        base_template=base_template,
        destination=destination,
        overwrite=overwrite,
    )
    typer.echo("Download de COTAHIST concluido.")


@download_app.command("carteiras")
def download_carteiras_cmd(
    urls: List[str] = typer.Option(..., "--urls", help="Entradas no formato URL,start,end[,arquivo.csv]"),
    destination: Path = typer.Option(Path("data") / "ibov_carteiras", help="Diretorio de destino"),
    overwrite: bool = typer.Option(False, help="Sobrescreve arquivos existentes"),
) -> None:
    """Baixa carteiras do Ibovespa a partir de especificacoes de URL e periodo."""

    specs = [_parse_carteira_entry(entry) for entry in urls]
    download_carteiras(
        specs,
        destination=destination,
        overwrite=overwrite,
    )
    typer.echo("Download de carteiras concluido.")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    app()

