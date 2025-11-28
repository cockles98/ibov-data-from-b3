
# 🇧🇷 B3 Historical Data Pipeline (ETL)

> **Automated ingestion, parsing, and normalization of Brazilian Stock Exchange (B3) historical data.**

This repository contains a robust ETL (Extract, Transform, Load) pipeline designed to process the massive, legacy-formatted datasets provided by B3 (formerly BM&FBovespa). It serves as the data backbone for quantitative research, solving the complexity of parsing fixed-width text files (`COTAHIST`) and standardizing market data for High-Frequency Trading (HFT) and Low-Latency simulations.

---

## 🎯 The Problem
Financial modeling requires pristine data. However, B3's historical data (Series Históricas) is distributed in raw, fixed-width text files that are:
1.  **Hard to Parse:** Legacy layouts with mixed data types and headers/trailers.
2.  **Voluminous:** Millions of daily records requiring efficient storage.
3.  **Dirty:** Requires adjustment for corporate events (splits/dividends) and odd-lot filtering.

## 🛠️ The Solution
This pipeline automates the entire lifecycle:
* **Extract:** Downloads raw `COTAHIST_AAAA.TXT` files directly from B3's servers.
* **Transform:** Parses the positional layout (Layout B3), handles decimal scaling, converts types, and filters by asset class (Stocks, Options, ETFs).
* **Load:** Saves optimized, query-ready data in **Parquet** (columnar storage) or SQL, ready for Pandas/Polars consumption.

---

## ⚡ Key Features

* **Fixed-Width Parsing:** High-performance parser for the B3 standard layout.
* **Asset Filtering:** Automatically separates "Odd Lot" (Fracionário) from "Round Lot" (Padrão).
* **Efficient Storage:** Converts gigabytes of text into compressed Parquet files (Snappy compression), reducing storage by ~70% and speeding up read times by 10x.
* **Ticker Normalization:** Cleans tickers (removes trailing spaces) and handles currency changes (BRL/CR$/etc) if dealing with very old data.

---

## 🚀 Usage

### 1. Installation
```bash
git clone [https://github.com/cockles98/ibov-data-from-b3.git](https://github.com/cockles98/ibov-data-from-b3.git)
pip install -r requirements.txt
````

### 2\. Run the Pipeline

To download and process the data for a specific year (e.g., 2024):

```bash
# Example CLI usage
python src/pipeline.py --year 2024 --output-format parquet
```

### 3\. Load in Python (Pandas)

```python
import pandas as pd

# Read the optimized parquet file
df = pd.read_parquet("data/processed/b3_2024.parquet")

# Filter for Petrobras (PETR4)
petr4 = df[df['ticker'] == 'PETR4']
print(petr4.head())
```

-----

## 📊 Data Schema (Output)

The processed data follows a strict schema optimized for Quant libraries:

| Column | Type | Description |
| :--- | :--- | :--- |
| `date` | `datetime64[ns]` | Session date |
| `ticker` | `string` | Asset symbol (e.g., VALE3) |
| `open` | `float64` | Opening price |
| `high` | `float64` | Highest price |
| `low` | `float64` | Lowest price |
| `close` | `float64` | Closing price (Last trade) |
| `volume` | `float64` | Financial volume |
| `quantity` | `int64` | Number of shares traded |

-----

## 🏗️ Tech Stack

  * **Python 3.10+**
  * **Pandas / Polars:** For vectorized data manipulation.
  * **PyArrow:** For writing high-performance Parquet files.
  * **Requests:** For reliable downloading from B3 public endpoints.