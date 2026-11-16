"""Bandwidth sweep + heteroskedasticity check for the AGROYIELD-ADAPT pilot.

Two questions:
 1. At what bandwidth does local weighting stop being a copy of global conformal?
 2. Is there any residual-scale heterogeneity in the Zambia records for a
    localizer to exploit? If |residual| is roughly constant, no weighting
    scheme can narrow valid intervals.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression

import pilot_zambia as P

ALPHA = P.ALPHA
SEED = P.SEED


def main():
    z = P.load()
    rng = np.random.default_rng(SEED)
    km = KMeans(n_clusters=15, n_init=10, random_state=SEED).fit(
        z[["lon", "lat"]].to_numpy())
    groups = km.labels_
    uniq = np.unique(groups)
    rng.shuffle(uniq)
    hold = np.array_split(uniq, 3)[0]
    test = np.isin(groups, hold)
    rest = ~test
    g_rest = np.unique(groups[rest])
    rng.shuffle(g_rest)
    cal = np.isin(groups, g_rest[: max(1, len(g_rest) // 3)]) & rest
    tr = rest & ~cal

    trd, cad, ted = z[tr], z[cal], z[test]
    Etr, Eca, Mtr, Mca, Ctr, Cca = P.prep(trd, cad)
    _, Ete, _, Mte, _, Cte = P.prep(trd, ted)
    X = lambda E, M, C: np.column_stack([E, M, C])          # noqa: E731

    rf = RandomForestRegressor(n_estimators=400, min_samples_leaf=5,
                              random_state=SEED, n_jobs=-1)
    rf.fit(X(Etr, Mtr, Ctr), trd["y"].to_numpy())
    f_tr = rf.predict(X(Etr, Mtr, Ctr))
    f_ca = rf.predict(X(Eca, Mca, Cca))
    f_te = rf.predict(X(Ete, Mte, Cte))
    a_tr = np.abs(trd["y"].to_numpy() - f_tr)
    a_ca = np.abs(cad["y"].to_numpy() - f_ca)
    y_te = ted["y"].to_numpy()

    print(f"fold 0: train={tr.sum()} cal={cal.sum()} test={test.sum()}")
    print(f"|residual| on calibration: mean={a_ca.mean():.0f} "
          f"sd={a_ca.std(ddof=0):.0f} cv={a_ca.std(ddof=0)/a_ca.mean():.3f}")
    print(f"|residual| on test: mean={np.abs(y_te-f_te).mean():.0f}")
    print()

    # --- Is residual scale predictable from features at all? ---
    Xca = X(Eca, Mca, Cca)
    lr = LinearRegression().fit(Xca, a_ca)
    r2 = lr.score(Xca, a_ca)
    print(f"linear R^2 for predicting |residual| from features: {r2:.3f}")

    dE = P.block_dist(Ete, Eca)
    dM = 0.5 * P.block_dist(Mte, Mca) + 0.5 * P.cat_dist(Cte, Cca)
    mE = np.median(dE[dE > 0])
    mM = np.median(dM[dM > 0])
    print(f"median nonzero distance: env={mE:.3f} mgmt={mM:.3f}")
    print()

    hdr = f"{'mult':>5s} {'hE':>7s} {'hM':>7s} {'cov':>6s} {'medW':>8s} {'meanESS':>8s} {'wgt_cv':>7s}"
    print(hdr)
    print("-" * len(hdr))
    for mult in (0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0):
        W = P.kernel(dE, mE * mult) * P.kernel(dM, mM * mult)
        qs, ess = [], []
        for i in range(len(y_te)):
            q, e = P.local_q(a_ca, W[i], ALPHA)
            qs.append(q)
            ess.append(e)
        qs = np.array(qs)
        r = P.eval_intervals(y_te, f_te - qs, f_te + qs, ALPHA)
        wcv = float(np.mean(W.std(axis=1) / np.maximum(W.mean(axis=1), 1e-9)))
        print(f"{mult:5.2f} {mE*mult:7.3f} {mM*mult:7.3f} {r['coverage']:6.3f} "
              f"{r['width_med']:8.1f} {np.mean(ess):8.1f} {wcv:7.3f}")

    # --- group-level residual scale spread (is there scale heterogeneity?) ---
    print()
    g_cal = groups[cal]
    resid_cal = np.abs(cad["y"].to_numpy() - f_ca)
    gs = [np.median(resid_cal[g_cal == g])
          for g in np.unique(g_cal) if (g_cal == g).sum() >= 20]
    print("group-level median |residual| (cal, groups with n>=20):")
    print("  ", np.round(sorted(gs), 0))
    if len(gs) > 1 and min(gs) > 0:
        print(f"  spread (max/min): {max(gs) / min(gs):.2f}x")


if __name__ == "__main__":
    main()
