"""
cleaner.py — Veri temizleme işlemleri modülü.
Komutlara göre DataFrame üzerinde temizleme yapar.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def clean_missing(df: pd.DataFrame, method: str = "drop", column: str = None) -> Tuple[pd.DataFrame, str]:
    """
    Eksik değerleri temizler.
    Yöntemler: drop, fill mean, fill median, fill ffill, fill bfill, fill 0
    """
    original_shape = df.shape[0]

    if method == "drop":
        if column:
            df = df.dropna(subset=[column])
            removed = original_shape - df.shape[0]
            return df, f"✅ '{column}' sütunundaki eksik değerler silindi. {removed} satır kaldırıldı."
        else:
            df = df.dropna()
            removed = original_shape - df.shape[0]
            return df, f"✅ Tüm eksik değerli satırlar silindi. {removed} satır kaldırıldı."

    elif method.startswith("fill"):
        fill_method = method.replace("fill ", "").replace("fill", "").strip()

        if fill_method == "mean":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if column and column in numeric_cols:
                count = df[column].isnull().sum()
                df[column] = df[column].fillna(df[column].mean())
                return df, f"✅ '{column}' sütunu ortalama ile dolduruldu. {count} hücre güncellendi."
            else:
                count = df[numeric_cols].isnull().sum().sum()
                df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                return df, f"✅ Sayısal sütunlar ortalama ile dolduruldu. {count} hücre güncellendi."

        elif fill_method == "median":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if column and column in numeric_cols:
                count = df[column].isnull().sum()
                df[column] = df[column].fillna(df[column].median())
                return df, f"✅ '{column}' sütunu medyan ile dolduruldu. {count} hücre güncellendi."
            else:
                count = df[numeric_cols].isnull().sum().sum()
                df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
                return df, f"✅ Sayısal sütunlar medyan ile dolduruldu. {count} hücre güncellendi."

        elif fill_method == "ffill":
            count = df.isnull().sum().sum()
            df = df.ffill()
            return df, f"✅ Eksik değerler önceki değerle dolduruldu. {count} hücre güncellendi."

        elif fill_method == "bfill":
            count = df.isnull().sum().sum()
            df = df.bfill()
            return df, f"✅ Eksik değerler sonraki değerle dolduruldu. {count} hücre güncellendi."

        elif fill_method == "0":
            count = df.isnull().sum().sum()
            df = df.fillna(0)
            return df, f"✅ Eksik değerler 0 ile dolduruldu. {count} hücre güncellendi."

        else:
            return df, f"❌ Bilinmeyen doldurma yöntemi: '{fill_method}'. Kullanılabilir: mean, median, ffill, bfill, 0"

    return df, "❌ Bilinmeyen yöntem. Kullanılabilir: drop, fill mean, fill median, fill ffill, fill bfill, fill 0"


def clean_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    """Tekrar eden satırları siler."""
    original_shape = df.shape[0]
    df = df.drop_duplicates()
    removed = original_shape - df.shape[0]
    return df, f"✅ {removed} tekrar eden satır silindi. Kalan: {df.shape[0]} satır."


def clean_whitespace(df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    """String sütunlarındaki başta/sonda boşlukları temizler."""
    count = 0
    for col in df.select_dtypes(include=["object"]).columns:
        mask = df[col].dropna().apply(lambda x: str(x) != str(x).strip())
        count += mask.sum()
        df[col] = df[col].apply(lambda x: str(x).strip() if isinstance(x, str) else x)

    return df, f"✅ {count} hücredeki gereksiz boşluklar temizlendi."


def clean_outliers(df: pd.DataFrame, method: str = "zscore") -> Tuple[pd.DataFrame, str]:
    """Aykırı değerleri temizler. Yöntemler: zscore, iqr"""
    original_shape = df.shape[0]

    if method == "zscore":
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        mask = pd.Series([True] * len(df), index=df.index)

        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) < 3:
                continue
            mean = col_data.mean()
            std = col_data.std()
            if std == 0:
                continue
            z_scores = np.abs((df[col] - mean) / std)
            mask = mask & ((z_scores <= 3) | df[col].isnull())

        df = df[mask]
        removed = original_shape - df.shape[0]
        return df, f"✅ Z-score yöntemiyle {removed} aykırı değer satırı silindi."

    elif method == "iqr":
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        mask = pd.Series([True] * len(df), index=df.index)

        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            mask = mask & ((df[col] >= lower) & (df[col] <= upper) | df[col].isnull())

        df = df[mask]
        removed = original_shape - df.shape[0]
        return df, f"✅ IQR yöntemiyle {removed} aykırı değer satırı silindi."

    return df, f"❌ Bilinmeyen yöntem: '{method}'. Kullanılabilir: zscore, iqr"
