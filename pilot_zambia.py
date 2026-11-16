"""AGROYIELD-ADAPT feasibility pilot on the real Zambia records.

Purpose: before any proposal claim is written, test empirically whether
environment-only (C1), management-only (C2) or composite (C3) local weighting
beats global split conformal (C0) under spatial holdout.

This is a pilot, not the prespecified experiment: 3 spatial folds, one seed,
bandwidths chosen on inner calibration data, no buffer, no C5 calibrated
benchmark. It answers the feasibility question (does the effect have any
signal here?) and nothing more.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans

CSV = "One_Acre_Fund_MEL_maize_survey_data_2016-2022.csv"
ALPHA = 0.10
SEED = 0

ENV_NUM = ["lon", "lat", "season_prec", "season_prec_1", "season_prec_2",
           "season_prec_3", "avg_season_gdd", "avg_season_ai",
           "avg_season_tavg", "elev", "twi", "soil_rzpawhc", "soil_clay",
           "soil_pH", "soil_orgC", "soil_ECEC"]
MGMT_NUM = ["N_kg_ha", "P_kg_ha", "K_kg_ha", "pl_m2", "row_spacing"]
MGMT_CAT = ["hybrid", "hyb_type", "hyb_mat", "hyb_tol_msv", "fert_in_hole",
            "weeding", "pesticide", "pest", "compost"]


def load():
    df = pd.read_csv(CSV)
    z = df[df["iso"] == "ZMB"].copy()
    z["y"] = z["yield_kg_ha"].astype(float)
    for c in ENV_NUM + MGMT_NUM:
        z[c] = pd.to_numeric(z[c], errors="coerce")
    for c in MGMT_CAT:
        z[c] = z[c].map(
            lambda v: "NA" if pd.isna(v) else (str(v).strip() or "NA"))
    return z


def prep(train, other):
    """Fit imputation/scaling on train only; return design matrices."""
    med = {c: train[c].median() for c in ENV_NUM + MGMT_NUM}
    med = {c: (0.0 if pd.isna(v) else v) for c, v in med.items()}
    sd = {}
    for c in ENV_NUM + MGMT_NUM:
        s = train[c].fillna(med[c]).std(ddof=0)
        sd[c] = s if s and s > 0 else 1.0
    levels = {c: sorted(train[c].unique()) for c in MGMT_CAT}

    def num(d, cols):
        return np.column_stack([((d[c].fillna(med[c]) - med[c]) / sd[c]).to_numpy()
                                for c in cols])

    def cat(d):
        return np.column_stack(
            [d[c].map({v: i for i, v in enumerate(levels[c])}).fillna(-1).to_numpy()
             for c in MGMT_CAT])

    return [num(d, ENV_NUM) for d in (train, other)] + \
           [num(d, MGMT_NUM) for d in (train, other)] + \
           [cat(d) for d in (train, other)]


def block_dist(Xa, Xb):
    """Mean squared scaled difference per feature (cat: 0/1 mismatch mean)."""
    d = (Xa[:, None, :] - Xb[None, :, :]) ** 2
    return d.mean(axis=2)


def cat_dist(Ca, Cb):
    return (Ca[:, None, :] != Cb[None, :, :]).mean(axis=2)


def kernel(d2, h):
    return np.exp(-d2 / (2.0 * h ** 2))


def local_q(resid, w, alpha):
    """baseLCP: >=1-alpha weighted quantile incl. self atom at +inf."""
    order = np.argsort(resid)
    r = resid[order]
    w = w[order]
    d = w.sum() + 1.0                      # include test-point self weight
    p = w / d
    p_test = 1.0 / d
    cum = np.cumsum(p)
    target = 1.0 - alpha
    finite = r[cum >= target]
    q = finite[0] if finite.size else np.inf
    # if the infinite atom alone already reaches the target mass, q is inf
    if p_test >= target:
        q = np.inf
    return q, (w.sum() ** 2) / (w ** 2).sum() if (w ** 2).sum() > 0 else 0.0


def eval_intervals(y, lo, hi, alpha):
    width = hi - lo
    finite = np.isfinite(width)
    cov = float(np.mean((y >= lo) & (y <= hi)))
    out = {
        "coverage": cov,
        "cover_n": int(np.sum((y >= lo) & (y <= hi))),
        "frac_inf": float(1 - finite.mean()),
        "width_med": float(np.median(width[finite])) if finite.any() else np.inf,
    }
    score = width + (2 / alpha) * np.where(y < lo, lo - y, 0) + \
        (2 / alpha) * np.where(y > hi, y - hi, 0)
    out["interval_score_med"] = float(np.median(score[np.isfinite(score)])) \
        if np.isfinite(score).any() else np.inf
    return out


def main():
    z = load()
    rng = np.random.default_rng(SEED)
    xy = z[["lon", "lat"]].to_numpy()
    km = KMeans(n_clusters=15, n_init=10, random_state=SEED).fit(xy)
    groups = km.labels_
    uniq = np.unique(groups)
    rng.shuffle(uniq)
    folds = np.array_split(uniq, 3)

    results = {k: [] for k in ["C0", "C1", "C2", "C3"]}
    ess_log = {k: [] for k in ["C1", "C2", "C3"]}

    for fi, hold in enumerate(folds):
        test = np.isin(groups, hold)
        rest = ~test
        g_rest = np.unique(groups[rest])
        rng.shuffle(g_rest)
        cal_g = g_rest[: max(1, len(g_rest) // 3)]
        cal = np.isin(groups, cal_g) & rest
        tr = rest & ~cal

        trd, cad, ted = z[tr], z[cal], z[test]
        # prep works pairwise; call explicitly (stats fit on train only)
        Etr, Eca, Mtr, Mca, Ctr, Cca = prep(trd, cad)
        Etr2, Ete, Mtr2, Mte, Ctr2, Cte = prep(trd, ted)
        assert np.allclose(Etr, Etr2)

        def X(E, M, C):
            return np.column_stack([E, M, C])

        rf = RandomForestRegressor(n_estimators=400, min_samples_leaf=5,
                                   random_state=SEED, n_jobs=-1)
        rf.fit(X(Etr, Mtr, Ctr), trd["y"].to_numpy())
        f_tr = rf.predict(X(Etr, Mtr, Ctr))
        f_ca = rf.predict(X(Eca, Mca, Cca))
        f_te = rf.predict(X(Ete, Mte, Cte))
        a_tr = np.abs(trd["y"].to_numpy() - f_tr)
        a_ca = np.abs(cad["y"].to_numpy() - f_ca)
        y_te = ted["y"].to_numpy()

        # global conformal (C0)
        n = len(a_ca)
        k = int(np.ceil((n + 1) * (1 - ALPHA)))
        q0 = np.sort(a_ca)[k - 1] if k <= n else np.inf
        results["C0"].append(eval_intervals(y_te, f_te - q0, f_te + q0, ALPHA))

        dE = block_dist(Ete, Eca)
        dM = block_dist(Mte, Mca)
        dMc = cat_dist(Cte, Cca)

        med_h = {}
        for name, dd in (("E", dE), ("M", dM)):
            med_h[name] = np.median(dd[dd > 0]) if np.any(dd > 0) else 1.0

        # small frozen grid on inner data (train vs cal), pick by inner score
        best = {}
        for name in ("E", "M"):
            cands = [0.5, 1.0, 2.0]
            scores = []
            if name == "E":
                di = block_dist(Eca, Etr)
            else:
                di = 0.5 * block_dist(Mca, Mtr) + 0.5 * cat_dist(Cca, Ctr)
            for mult in cands:
                h = med_h[name] * mult
                W = kernel(di, h)
                qs = []
                for i in range(len(a_ca)):
                    w = W[i]
                    q, _ = local_q(a_tr, w, ALPHA)
                    qs.append(q)
                lo = f_ca - np.array(qs)
                hi = f_ca + np.array(qs)
                scores.append(eval_intervals(cad["y"].to_numpy(), lo, hi,
                                             ALPHA)["interval_score_med"])
            best[name] = med_h[name] * cands[int(np.nanargmin(scores))]

        variants = {
            "C1": kernel(dE, best["E"]),
            "C2": kernel(0.5 * dM + 0.5 * dMc, best["M"]),
            "C3": kernel(dE, best["E"]) * kernel(0.5 * dM + 0.5 * dMc, best["M"]),
        }
        for name, W in variants.items():
            qs, esss = [], []
            for i in range(len(y_te)):
                q, e = local_q(a_ca, W[i], ALPHA)
                qs.append(q)
                esss.append(e)
            qs = np.array(qs)
            results[name].append(
                eval_intervals(y_te, f_te - qs, f_te + qs, ALPHA))
            ess_log[name].append(float(np.mean(esss)))

    print(f"Zambia records: {len(z)} | spatial groups: 15 | folds: 3 | "
          f"alpha={ALPHA} | seed={SEED}\n")
    hdr = f"{'method':6s} {'coverage':>9s} {'frac_inf':>9s} {'medianW':>10s} {'medIS':>10s} {'meanESS':>8s}"
    print(hdr)
    print("-" * len(hdr))
    for m, rows in results.items():
        cov = np.mean([r["coverage"] for r in rows])
        fi_ = np.mean([r["frac_inf"] for r in rows])
        w = np.mean([r["width_med"] for r in rows])
        is_ = np.mean([r["interval_score_med"] for r in rows])
        ess = np.mean(ess_log[m]) if m in ess_log else float("nan")
        print(f"{m:6s} {cov:9.3f} {fi_:9.3f} {w:10.1f} {is_:10.1f} {ess:8.1f}")
    print("\nPer-fold coverage:")
    for m, rows in results.items():
        print(f"  {m}: " + ", ".join(f"{r['coverage']:.3f} (inf {r['frac_inf']:.2f})"
                                     for r in rows))


if __name__ == "__main__":
    main()
