"""Module 1 - split integrity.

Compares the same model and features under three validation designs:

    random   - KFold ignoring spatial/temporal structure (what many papers report)
    cluster  - GroupKFold on rounded coordinate + year
    country  - leave-one-country-out (GroupKFold on country)

The difference between the first and the others is the *inflation*: how much of
the reported skill comes from evaluation design rather than from a model that
would transport to new fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, GroupKFold

from ..schema import NUM, build_matrix, cluster_key, load_panel

DESIGNS = ("random", "cluster", "country")


@dataclass
class SplitResult:
    design: str
    folds: int
    r2_log: float
    rmse_kg_ha: float
    n_train: list[int] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "design": self.design,
            "folds": self.folds,
            "r2_log": round(self.r2_log, 4),
            "rmse_kg_ha": round(self.rmse_kg_ha, 1),
        }


def make_splits(design: str, df: pd.DataFrame, n_splits: int = 5,
                seed: int = 0) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return (train_idx, test_idx) pairs for one validation design."""
    idx = np.arange(len(df))
    if design == "random":
        return list(KFold(n_splits, shuffle=True, random_state=seed).split(idx))
    if design == "cluster":
        groups = cluster_key(df)
        n = min(n_splits, len(np.unique(groups)))
        return list(GroupKFold(n).split(idx, groups=groups))
    if design == "country":
        groups = df["country"].to_numpy()
        n = len(np.unique(groups))
        return list(GroupKFold(n).split(idx, groups=groups))
    raise ValueError(f"unknown design {design!r}; expected one of {DESIGNS}")


def _prepare_fold(X: pd.DataFrame, tr: np.ndarray, te: np.ndarray):
    """Fold-internal median imputation with missingness flags.

    Imputing before splitting would leak test-set statistics into training and
    would itself inflate the random-minus-cluster gap.
    """
    Xtr, Xte = X.iloc[tr].copy(), X.iloc[te].copy()
    for col in NUM:
        med = Xtr[col].median()
        Xtr[col + "_isna"] = Xtr[col].isna().astype(float)
        Xte[col + "_isna"] = Xte[col].isna().astype(float)
        Xtr[col] = Xtr[col].fillna(med).fillna(0.0)
        Xte[col] = Xte[col].fillna(med).fillna(0.0)
    return Xtr, Xte


def r2_score(y: np.ndarray, p: np.ndarray) -> float:
    ss_tot = ((y - y.mean()) ** 2).sum()
    if ss_tot == 0:
        return float("nan")
    return float(1.0 - ((y - p) ** 2).sum() / ss_tot)


def evaluate(design: str, df: pd.DataFrame, X: pd.DataFrame, ly: np.ndarray,
             trees: int = 250, seed: int = 0, n_splits: int = 5) -> SplitResult:
    """Fit the same random forest under one validation design."""
    pred = np.zeros(len(df))
    seen = np.zeros(len(df), dtype=bool)
    folds = make_splits(design, df, n_splits=n_splits, seed=seed)
    for tr, te in folds:
        Xtr, Xte = _prepare_fold(X, tr, te)
        model = RandomForestRegressor(
            n_estimators=trees, min_samples_leaf=5, n_jobs=-1, random_state=seed
        ).fit(Xtr, ly[tr])
        pred[te] = model.predict(Xte)
        seen[te] = True
    if not seen.all():
        raise RuntimeError(f"{design}: {int((~seen).sum())} rows were never tested")
    rmse = float(np.sqrt(np.mean((np.expm1(ly) - np.expm1(pred)) ** 2)))
    return SplitResult(
        design=design,
        folds=len(folds),
        r2_log=r2_score(ly, pred),
        rmse_kg_ha=rmse,
        n_train=[len(tr) for tr, _ in folds],
    )


def duplication_stats(df: pd.DataFrame) -> dict:
    """How much of the panel is repeated at the same location and year."""
    dup = df.duplicated(subset=["lon", "lat", "year"], keep=False)
    return {
        "rows": int(len(df)),
        "rows_sharing_coord_year": int(dup.sum()),
        "pct_sharing_coord_year": round(100 * float(dup.mean()), 1),
        "clusters": int(len(np.unique(cluster_key(df)))),
        "countries": int(df["country"].nunique()),
    }


def audit_splits(df: pd.DataFrame, designs: tuple[str, ...] = DESIGNS,
                 trees: int = 250, seed: int = 0) -> dict:
    """Run every design and report inflation relative to the random split."""
    X, _, ly = build_matrix(df)
    results = {d: evaluate(d, df, X, ly, trees=trees, seed=seed) for d in designs}
    base = results["random"].r2_log
    out = {
        "stats": duplication_stats(df),
        "results": {d: r.as_dict() for d, r in results.items()},
        "inflation": {
            d: round(base - r.r2_log, 4)
            for d, r in results.items() if d != "random"
        },
    }
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Split-integrity audit")
    ap.add_argument("--data", required=True)
    ap.add_argument("--trees", type=int, default=250)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json", default=None, help="write the result as JSON")
    args = ap.parse_args(argv)

    df = load_panel(args.data)
    rep = audit_splits(df, trees=args.trees, seed=args.seed)

    s = rep["stats"]
    print(f"rows {s['rows']}  clusters {s['clusters']}  countries {s['countries']}")
    print(f"rows sharing a coordinate-year cluster: "
          f"{s['rows_sharing_coord_year']} ({s['pct_sharing_coord_year']}%)")
    print()
    print(f"{'design':10s} {'folds':>5s} {'R2(log)':>9s} {'RMSE kg/ha':>11s}")
    for d, r in rep["results"].items():
        print(f"{d:10s} {r['folds']:5d} {r['r2_log']:+9.3f} {r['rmse_kg_ha']:11.0f}")
    print()
    for d, v in rep["inflation"].items():
        print(f"inflation from ignoring {d:8s} structure: {v:+.3f} R2")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=2)
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
