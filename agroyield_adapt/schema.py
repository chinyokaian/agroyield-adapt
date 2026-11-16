"""Panel loading and feature definitions for the AGROYIELD-ADAPT auditor.

The feature blocks and preprocessing rules mirror the published analysis of the
One Acre Fund panel (Aramburu Merlos et al. 2024, Zenodo 10.5281/zenodo.11122388)
so that results are comparable with the dataset's own source paper.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__version__ = "0.1.0"

#: Continuous predictors, grouped by the block they belong to.
CLIMATE = [
    "avg_season_gdd", "avg_season_ai", "avg_season_tavg", "season_prec",
    "season_prec_1", "season_prec_2", "season_prec_3", "elev", "twi",
]
SOIL = ["soil_rzpawhc", "soil_clay", "soil_pH", "soil_orgC", "soil_ECEC"]
MANAGEMENT = [
    "N_kg_ha", "P_kg_ha", "K_kg_ha", "lime_kg_ha", "pl_m2",
    "row_spacing", "plant_doy", "plant_date_dev", "hyb_mat",
]
NUM = CLIMATE + SOIL + MANAGEMENT
BIN = [
    "hybrid", "compost", "weeding", "pesticide",
    "fert_in_hole", "disease", "pest", "water_excess",
]
TARGET = "yield_kg_ha"


def to_bin(series: pd.Series) -> pd.Series:
    """Map the dataset's mixed boolean encodings onto 0/1 floats."""
    if series.dtype == bool:
        return series.astype(float)
    return series.astype(str).str.upper().map(
        {"TRUE": 1.0, "FALSE": 0.0, "1": 1.0, "0": 0.0, "YES": 1.0, "NO": 0.0}
    )


def load_panel(path: str) -> pd.DataFrame:
    """Read the survey panel; rows with a missing or negative yield are dropped."""
    df = pd.read_csv(path, low_memory=False)
    df = df[df[TARGET].notna() & (df[TARGET] >= 0)].reset_index(drop=True)
    return df


def build_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Return (X, y, log1p(y)) for the modelled feature set."""
    X = df[NUM].astype(float).copy()
    for col in BIN:
        X[col] = to_bin(df[col]).fillna(0.0)
    y = df[TARGET].astype(float).to_numpy()
    return X, y, np.log1p(y)


def cluster_key(df: pd.DataFrame, decimals: int = 1) -> np.ndarray:
    """Spatial-temporal cluster id: rounded coordinates plus survey year.

    Two rows sharing a cluster are not independent observations: they are either
    the same field measured twice or neighbouring fields recorded at one location.
    """
    return (
        df["lon"].round(decimals).astype(str)
        + "_"
        + df["lat"].round(decimals).astype(str)
        + "_"
        + df["year"].astype(str)
    ).to_numpy()
