"""
analyzer.py — Veri kalitesi analiz modülü.
Eksik değerler, duplike satırlar, boşluklar, tip uyumsuzlukları ve aykırı değerleri tespit eder.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any


def analyze_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    DataFrame'i kapsamlı bir şekilde analiz eder ve sorun raporu üretir.
    """
    report = {
        "shape": {"rows": df.shape[0], "columns": df.shape[1]},
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing": _analyze_missing(df),
        "duplicates": _analyze_duplicates(df),
        "whitespace": _analyze_whitespace(df),
        "outliers": _analyze_outliers(df),
        "summary": _generate_summary(df),
    }

    report["issues_found"] = _count_total_issues(report)
    report["commands"] = _suggest_commands(report)

    return report


def _analyze_missing(df: pd.DataFrame) -> Dict[str, Any]:
    """Eksik değer analizi."""
    missing_counts = df.isnull().sum()
    missing_pct = (df.isnull().sum() / len(df) * 100).round(2)

    details = {}
    for col in df.columns:
        if missing_counts[col] > 0:
            details[col] = {
                "count": int(missing_counts[col]),
                "percentage": float(missing_pct[col]),
            }

    return {
        "total": int(missing_counts.sum()),
        "columns_affected": len(details),
        "details": details,
    }


def _analyze_duplicates(df: pd.DataFrame) -> Dict[str, Any]:
    """Tekrar eden satır analizi."""
    dup_count = df.duplicated().sum()
    return {
        "total": int(dup_count),
        "percentage": round(dup_count / len(df) * 100, 2) if len(df) > 0 else 0,
    }


def _analyze_whitespace(df: pd.DataFrame) -> Dict[str, Any]:
    """String sütunlarında başta/sonda boşluk analizi."""
    details = {}
    total = 0

    for col in df.select_dtypes(include=["object"]).columns:
        has_whitespace = df[col].dropna().apply(
            lambda x: str(x) != str(x).strip() if isinstance(x, str) else False
        )
        count = has_whitespace.sum()
        if count > 0:
            details[col] = int(count)
            total += count

    return {
        "total": int(total),
        "columns_affected": len(details),
        "details": details,
    }


def _analyze_outliers(df: pd.DataFrame) -> Dict[str, Any]:
    """Sayısal sütunlardaki aykırı değer analizi (Z-score)."""
    details = {}
    total = 0

    for col in df.select_dtypes(include=[np.number]).columns:
        col_data = df[col].dropna()
        if len(col_data) < 3:
            continue

        mean = col_data.mean()
        std = col_data.std()
        if std == 0:
            continue

        z_scores = np.abs((col_data - mean) / std)
        outlier_count = (z_scores > 3).sum()

        if outlier_count > 0:
            details[col] = int(outlier_count)
            total += outlier_count

    return {
        "total": int(total),
        "columns_affected": len(details),
        "details": details,
    }


def _generate_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Genel veri özeti."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    text_cols = df.select_dtypes(include=["object"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

    return {
        "numeric_columns": len(numeric_cols),
        "text_columns": len(text_cols),
        "datetime_columns": len(datetime_cols),
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
    }


def _count_total_issues(report: Dict) -> int:
    """Toplam sorun sayısını hesaplar."""
    return (
        report["missing"]["total"]
        + report["duplicates"]["total"]
        + report["whitespace"]["total"]
        + report["outliers"]["total"]
    )


def _suggest_commands(report: Dict) -> List[Dict[str, str]]:
    """Sorunlara göre temizleme komutları önerir."""
    commands = []

    if report["missing"]["total"] > 0:
        commands.append({
            "issue": f"🔴 {report['missing']['total']} eksik değer ({report['missing']['columns_affected']} sütun)",
            "commands": [
                "clean --missing drop        → Eksik satırları sil",
                "clean --missing fill mean   → Ortalama ile doldur",
                "clean --missing fill median → Medyan ile doldur",
                "clean --missing fill ffill  → Önceki değerle doldur",
            ],
        })

    if report["duplicates"]["total"] > 0:
        commands.append({
            "issue": f"🟠 {report['duplicates']['total']} tekrar eden satır (%{report['duplicates']['percentage']})",
            "commands": [
                "clean --duplicates          → Tekrar eden satırları sil",
            ],
        })

    if report["whitespace"]["total"] > 0:
        commands.append({
            "issue": f"🟡 {report['whitespace']['total']} hücrede gereksiz boşluk ({report['whitespace']['columns_affected']} sütun)",
            "commands": [
                "clean --whitespace          → Boşlukları temizle",
            ],
        })

    if report["outliers"]["total"] > 0:
        commands.append({
            "issue": f"🟣 {report['outliers']['total']} aykırı değer ({report['outliers']['columns_affected']} sütun)",
            "commands": [
                "clean --outliers zscore     → Z-score ile aykırı değerleri sil",
                "clean --outliers iqr        → IQR yöntemi ile sil",
            ],
        })

    if not commands:
        commands.append({
            "issue": "✅ Veri temiz görünüyor! Sorun tespit edilmedi.",
            "commands": [],
        })

    return commands


def format_report_for_terminal(report: Dict) -> str:
    """Raporu terminal çıktısı için formatlar."""
    lines = []
    lines.append("")
    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append("║              📊  VERİ ANALİZ RAPORU                        ║")
    lines.append("╚══════════════════════════════════════════════════════════════╝")
    lines.append("")
    lines.append(f"  Satır sayısı  : {report['shape']['rows']}")
    lines.append(f"  Sütun sayısı  : {report['shape']['columns']}")
    lines.append(f"  Bellek kullanımı: {report['summary']['memory_usage_mb']} MB")
    lines.append(f"  Sayısal sütun : {report['summary']['numeric_columns']}")
    lines.append(f"  Metin sütun   : {report['summary']['text_columns']}")
    lines.append("")
    lines.append("──────────────────────────────────────────────────────────────")
    lines.append(f"  TOPLAM SORUN  : {report['issues_found']}")
    lines.append("──────────────────────────────────────────────────────────────")
    lines.append("")

    for cmd_group in report["commands"]:
        lines.append(f"  {cmd_group['issue']}")
        for cmd in cmd_group["commands"]:
            lines.append(f"    ➤  {cmd}")
        lines.append("")

    lines.append("──────────────────────────────────────────────────────────────")
    lines.append("  💡 Komut girin veya 'help' yazın  |  'ask <soru>' ile LLM'e sorun")
    lines.append("──────────────────────────────────────────────────────────────")

    return "\n".join(lines)


def format_report_for_llm(report: Dict, df: pd.DataFrame) -> str:
    """Raporu LLM'e göndermek için metin formatına çevirir."""
    lines = []
    lines.append(f"Dataset: {report['shape']['rows']} rows x {report['shape']['columns']} columns")
    lines.append(f"Columns: {', '.join(report['columns'])}")
    lines.append(f"Data types: {report['dtypes']}")
    lines.append(f"Missing values: {report['missing']['total']} (details: {report['missing']['details']})")
    lines.append(f"Duplicates: {report['duplicates']['total']}")
    lines.append(f"Whitespace issues: {report['whitespace']['total']}")
    lines.append(f"Outliers: {report['outliers']['total']}")
    lines.append(f"\nFirst 5 rows:\n{df.head().to_string()}")
    lines.append(f"\nDescribe:\n{df.describe().to_string()}")

    return "\n".join(lines)
