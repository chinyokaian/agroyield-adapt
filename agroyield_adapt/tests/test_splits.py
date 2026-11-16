"""Self-tests for module 1.

They use synthetic panels where the right answer is known, so the auditor can be
shown to detect inflation when it exists and to stay quiet when it does not.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from agroyield_adapt.checks.splits import (
    DESIGNS,
    audit_splits,
    duplication_stats,
    evaluate,
    make_splits,
    r2_score,
)
from agroyield_adapt.schema import build_matrix, cluster_key


def make_panel(n_clusters=100, rows_per_cluster=12, noise=20.0,
               seed=0) -> pd.DataFrame:
    """Duplicate rows that share an unobserved cluster-level effect.

    This is the mechanism that inflates reported skill in the real panel: several
    rows are recorded at one coordinate and year, so they share covariates *and*
    a field-level yield deviation. Six-day validation reads that shared deviation
    as model skill; validation that holds out the whole cluster cannot.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for c in range(n_clusters):
        x_c = rng.normal(0, 1)
        effect_c = rng.normal(0, 1000)          # shared, unobservable
        level = 3000 + 400 * x_c + effect_c
        for _ in range(rows_per_cluster):
            rows.append(
                {
                    "lon": 30.0 + 0.01 * c,
                    "lat": -1.0 - 0.01 * c,
                    "year": 2018,
                    "country": "A" if c % 2 == 0 else "B",
                    "yield_kg_ha": max(0.0, level + rng.normal(0, noise)),
                    "avg_season_tavg": x_c + rng.normal(0, 0.001),
                }
            )
    df = pd.DataFrame(rows)
    # remaining modelled columns exist but carry no signal
    from agroyield_adapt.schema import BIN, NUM

    for col in NUM:
        if col not in df.columns:
            df[col] = rng.normal(0, 1, len(df))
    for col in BIN:
        df[col] = rng.integers(0, 2, len(df)).astype(float)
    return df


def make_iid_panel(n=600, seed=0) -> pd.DataFrame:
    """No duplication and a genuine, transportable relationship: y = 2x."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame(
        {
            "lon": rng.uniform(30, 33, n),
            "lat": rng.uniform(-3, -1, n),
            "year": rng.choice([2017, 2018, 2019], n),
            "country": rng.choice(["A", "B", "C"], n),
            "yield_kg_ha": 2000.0,
            "avg_season_tavg": rng.normal(0, 1, n),
        }
    )
    df["yield_kg_ha"] = 2000 + 400 * df["avg_season_tavg"] + rng.normal(0, 60, n)
    from agroyield_adapt.schema import BIN, NUM

    for col in NUM:
        if col not in df.columns:
            df[col] = rng.normal(0, 1, n)
    for col in BIN:
        df[col] = rng.integers(0, 2, n).astype(float)
    return df


def test_cluster_key_groups_duplicates_together():
    df = pd.DataFrame(
        {
            "lon": [30.00, 30.04, 31.00],
            "lat": [-1.00, -1.03, -2.00],
            "year": [2018, 2018, 2019],
        }
    )
    key = cluster_key(df)
    assert key[0] == key[1], "rows 0.1 deg apart in the same year must share a cluster"
    assert key[0] != key[2]


def test_r2_score_edges():
    y = np.array([1.0, 2.0, 3.0])
    assert r2_score(y, y) == pytest.approx(1.0)
    assert r2_score(y, np.full_like(y, y.mean())) == pytest.approx(0.0)
    assert r2_score(y, y[::-1]) < 0


def test_duplication_stats_counts_repeats():
    df = make_panel(n_clusters=10, rows_per_cluster=2)
    stats = duplication_stats(df)
    assert stats["rows"] == 20
    assert stats["rows_sharing_coord_year"] == 20
    assert stats["pct_sharing_coord_year"] == 100.0


def test_random_split_leaks_and_cluster_split_does_not():
    """The auditor must find the inflation when duplication is present."""
    df = make_panel()
    X, _, ly = build_matrix(df)
    rand = evaluate("random", df, X, ly, trees=100)
    group = evaluate("cluster", df, X, ly, trees=100)
    assert rand.r2_log > 0.7, "reading duplicate clusters should look strong"
    assert group.r2_log < 0.5, "a held-out cluster cannot reveal its own effect"
    assert rand.r2_log - group.r2_log > 0.3


def test_inflation_is_small_without_duplication():
    """False-positive check: a genuinely transportable model keeps its skill."""
    df = make_iid_panel()
    X, _, ly = build_matrix(df)
    rand = evaluate("random", df, X, ly, trees=60)
    group = evaluate("cluster", df, X, ly, trees=60)
    assert rand.r2_log > 0.5
    assert abs(rand.r2_log - group.r2_log) < 0.15


def test_country_design_holds_out_whole_countries():
    df = make_iid_panel(n=300)
    folds = make_splits("country", df)
    assert len(folds) == df["country"].nunique()
    for tr, te in folds:
        held = set(df["country"].iloc[te])
        assert len(held) == 1
        assert held.isdisjoint(set(df["country"].iloc[tr]))


def test_every_row_is_tested_once_per_design():
    df = make_iid_panel(n=300)
    for design in DESIGNS:
        counts = np.zeros(len(df), dtype=int)
        for _, te in make_splits(design, df):
            counts[te] += 1
        assert (counts == 1).all(), f"{design} does not cover each row exactly once"


def test_audit_splits_reports_inflation_keys():
    df = make_panel(n_clusters=40, rows_per_cluster=12)
    rep = audit_splits(df, trees=80)
    assert set(rep["results"]) == set(DESIGNS)
    assert set(rep["inflation"]) == {"cluster", "country"}
    assert rep["inflation"]["cluster"] > 0.3
