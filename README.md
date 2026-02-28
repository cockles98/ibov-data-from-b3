# 🇧🇷 B3 Historical Data Pipeline (ETL)

> **Automated ingestion, parsing, and normalization of Brazilian Stock Exchange (B3) historical data.**

This repository contains a robust ETL pipeline for processing B3's legacy-formatted historical datasets (`COTAHIST`). It solves the unglamorous but critical problem of turning decades of fixed-width text files into clean, query-ready data — and serves as the data backbone behind the [Atlas quantitative strategy](https://github.com/cockles98/itau-quant-challenge-2025) and the [MFG market microstructure model](https://github.com/cockles98/mfg-for-financial-market).

---

## 🎯 The Problem

B3's historical data (Séries Históricas) spans decades of Brazilian market activity — but it's distributed in raw, fixed-width text files that are painful to work with:

- **Hard to parse:** Legacy positional layout with mixed data types, headers, and trailers
- **Voluminous:** Millions of daily records across multiple asset classes requiring efficient storage
- **Dirty:** Requires adjustment for corporate events (splits/dividends) and odd-lot filtering

Anyone doing serious quantitative research on Brazilian equities has dealt with this. This pipeline automates the entire lifecycle.

---

## 🛠️ The Solution

- **Extract:** Downloads raw `COTAHIST_AAAA.TXT` files directly from B3's public servers
- **Transform:** Parses the positional layout (B3 standard), handles decimal scaling, converts types, and filters by asset class (Stocks, Options, ETFs)
- **Load:** Saves optimized, query-ready data in **Parquet** (columnar storage) or SQL, ready for Pandas/Polars consumption

---

## ⚡ Key Features

- **Fixed-Width Parsing:** High-performance parser for the B3 standard layout
- **Asset Filtering:** Automatically separates odd-lot (Fracionário) from round-lot (Padrão) markets
- **Efficient Storage:** Converts gigabytes of text into compressed Parquet files (Snappy), reducing storage by ~70% and speeding up read times by 10x
- **Ticker Normalization:** Cleans tickers and handles legacy currency formats for historical data going back to 1986

---

## 🚀 Usage

### Installation
```bash
git clone https://github.com/cockles98/ibov-data-from-b3.git
pip install -r requirements.txt
```

### Run the Pipeline
```bash
# Download and process data for a specific year
python src/pipeline.py --year 2024 --output-format parquet
```

### Load in Python
```python
import pandas as pd

# Read the optimized parquet file
df = pd.read_parquet("data/processed/b3_2024.parquet")

# Filter for Petrobras (PETR4)
petr4 = df[df['ticker'] == 'PETR4']
print(petr4.head())
```

---

## 📊 Output Schema

| Column | Type | Description |
| :--- | :--- | :--- |
| `date` | `datetime64[ns]` | Session date |
| `ticker` | `string` | Asset symbol (e.g., VALE3) |
| `open` | `float64` | Opening price |
| `high` | `float64` | Highest price |
| `low` | `float64` | Lowest price |
| `close` | `float64` | Closing price (last trade) |
| `volume` | `float64` | Financial volume |
| `quantity` | `int64` | Number of shares traded |

---

## 🏗️ Tech Stack

- **Python 3.10+**
- **Pandas / Polars** — vectorized data manipulation
- **PyArrow** — high-performance Parquet I/O
- **Requests** — reliable downloading from B3 public endpoints

---

*Working with Brazilian market data and need help with data infrastructure or quantitative modeling? Feel free to reach out via [LinkedIn](https://www.linkedin.com/in/felipe-cockles) or [email](mailto:felipe.cockles@hotmail.com).*
