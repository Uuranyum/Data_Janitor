"""
file_handler.py — CSV ve Excel dosya okuma modülü.
"""

import pandas as pd
from pathlib import Path


def load_file(file_path: str) -> pd.DataFrame:
    """
    Verilen dosya yolundan CSV veya Excel dosyasını okur.
    Desteklenen formatlar: .csv, .xlsx, .xls
    """
    path = Path(file_path.strip().strip('"').strip("'"))

    if not path.exists():
        raise FileNotFoundError(f"Dosya bulunamadı: {path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path, engine="openpyxl")
    else:
        raise ValueError(f"Desteklenmeyen dosya formatı: {suffix}\nDesteklenen: .csv, .xlsx, .xls")

    return df


def export_file(df: pd.DataFrame, file_path: str) -> str:
    """
    DataFrame'i belirtilen dosya yoluna kaydeder.
    """
    path = Path(file_path.strip().strip('"').strip("'"))
    suffix = path.suffix.lower()

    if suffix == ".csv":
        df.to_csv(path, index=False)
    elif suffix in (".xlsx", ".xls"):
        df.to_excel(path, index=False, engine="openpyxl")
    else:
        # Default to CSV
        path = path.with_suffix(".csv")
        df.to_csv(path, index=False)

    return str(path)
