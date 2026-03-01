from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple, List
import math
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

# Truck calculation when volume not in CSV
VOLUME_PER_SHIPMENT_ASSUMED = 1200  # units per shipment
TRUCK_CAPACITY_UNITS = 10_000
PACKING_BUFFER = 1.10


@dataclass
class CsvAnalysisResult:
    summary: Dict[str, Any]
    kpis: Dict[str, Any]
    anomalies: pd.DataFrame
    cleaned_shape: Tuple[int, int]
    numeric_cols: List[str]


def analyze_csv(csv_path: str) -> CsvAnalysisResult:
    df = pd.read_csv(csv_path)
    original_shape = df.shape

    df.columns = [c.strip() for c in df.columns]
    df = df.dropna(how="all").copy()

    # Try to parse any column that looks like a date
    for c in df.columns:
        if "date" in c.lower() or "time" in c.lower():
            try:
                df[c] = pd.to_datetime(df[c], errors="ignore")
            except Exception:
                pass

    summary = {
        "rows_original": int(original_shape[0]),
        "cols_original": int(original_shape[1]),
        "rows_after_drop_empty": int(df.shape[0]),
        "missingness_top": df.isna().mean().sort_values(ascending=False).head(10).to_dict(),
        "column_dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "columns": list(df.columns),
    }

    # Real KPIs from the data (so the report shows actual numbers, not placeholders)
    kpis: Dict[str, Any] = {
        "total_shipments": int(df.shape[0]),
        "total_columns": int(df.shape[1]),
    }
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        kpis["numeric_columns_count"] = len(numeric_cols)

    # Counts for common operational columns (use actual column names if present)
    for col in ["unique_item_id", "item_id", "dispatch_location"]:
        if col in df.columns:
            missing = df[col].isna() | (df[col].astype(str).str.strip() == "")
            n_missing = int(missing.sum())
            n_valid = int((~missing).sum())
            kpis[f"shipments_with_missing_{col}"] = n_missing
            kpis[f"valid_shipments_{col}"] = n_valid
    if "unique_item_id" in df.columns:
        missing_uid = df["unique_item_id"].isna() | (df["unique_item_id"].astype(str).str.strip() == "")
        kpis["excluded_shipments_missing_unique_id"] = int(missing_uid.sum())
        kpis["valid_shipment_count"] = int((~missing_uid).sum())
    if "dispatch_location" in df.columns:
        loc_counts = df["dispatch_location"].value_counts()
        kpis["dispatch_location_breakdown"] = {str(k): int(v) for k, v in loc_counts.head(15).items()}
    if "item_name" in df.columns:
        item_counts = df["item_name"].value_counts()
        kpis["item_breakdown"] = {str(k): int(v) for k, v in item_counts.head(10).items()}

    # Required trucks: use volume column if present, else estimate from valid shipment count
    valid_count = kpis.get("valid_shipment_count", int(df.shape[0]))
    total_volume = None
    volume_col = None
    for c in df.columns:
        if "volume" in c.lower() and pd.api.types.is_numeric_dtype(df[c]):
            volume_col = c
            break
    if volume_col:
        total_volume = float(df[volume_col].sum())
        kpis["total_volume_units"] = int(round(total_volume))
        kpis["volume_source"] = "from_data"
    else:
        total_volume = valid_count * VOLUME_PER_SHIPMENT_ASSUMED
        kpis["estimated_volume_units"] = int(total_volume)
        kpis["volume_per_shipment_assumed"] = VOLUME_PER_SHIPMENT_ASSUMED
        kpis["volume_source"] = "estimated"

    if total_volume is not None:
        buffered = total_volume * PACKING_BUFFER
        kpis["required_trucks"] = max(1, math.ceil(buffered / TRUCK_CAPACITY_UNITS))
        kpis["buffered_volume_units"] = int(round(buffered))

    # Anomalies on numeric cols
    anomalies = pd.DataFrame()
    if len(numeric_cols) >= 2 and df.shape[0] >= 20:
        X = df[numeric_cols].replace([np.inf, -np.inf], np.nan).fillna(0.0).values
        model = IsolationForest(
            n_estimators=200,
            contamination=0.03,
            random_state=42,
        )
        preds = model.fit_predict(X)
        scores = model.decision_function(X)

        df_anom = df.copy()
        df_anom["is_anomaly"] = (preds == -1)
        df_anom["anomaly_score"] = scores

        anomalies = df_anom[df_anom["is_anomaly"]].sort_values("anomaly_score").head(25)

    return CsvAnalysisResult(
        summary=summary,
        kpis=kpis,
        anomalies=anomalies,
        cleaned_shape=df.shape,
        numeric_cols=numeric_cols,
    )
