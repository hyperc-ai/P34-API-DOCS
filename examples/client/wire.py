"""Wire (de)serialization helpers for the P34 API (parml-wire/2).

DataFrames cross the wire either as JSON lists of records or as
base64-encoded Parquet (dtypes survive intact; None becomes JSON null).
"""
from __future__ import annotations

import base64
import io
import json

import pandas as pd


def records(df: pd.DataFrame) -> list:
    """JSON-safe list of records (NaN/None -> null)."""
    return json.loads(df.to_json(orient="records"))


def df_to_b64(df: pd.DataFrame | None) -> str | None:
    if df is None:
        return None
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    buf = io.BytesIO()
    df.reset_index(drop=True).to_parquet(buf, index=False)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def b64_to_df(blob: str | None) -> pd.DataFrame | None:
    if blob is None:
        return None
    return pd.read_parquet(io.BytesIO(base64.b64decode(blob.encode("ascii"))))
