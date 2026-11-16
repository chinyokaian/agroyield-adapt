import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import NearestNeighbors
from scipy.stats import spearmanr, wasserstein_distance
exec(open("pilot_full.py").read().split("ALPHA = 0.10")[0])  # reuse data/X/y/helpers

ALPHA=0.10
rows=[]
for seed in [0,1,2]:
    for c in sorted(df.country.unique()):
        te_all=np.where(df.country.values==c)[0]; tr_all=np.where(df.country.values!=c)[0]
        rng=np.random.default_rng(seed)
        te_all=rng.permutation(te_all); te,cal_i=te_all[:len(te_all)//2],te_all[len(te_all)//2:]
        tr_all=rng.permutation(tr_all); ncal=max(len(tr_all)//3,200)
        cal,tr=tr_all[:ncal],tr_all[ncal:]
        Xtr,Xc=prep_fold(tr,cal); _,Xt=prep_fold(tr,te); _,Xci=prep_fold(tr,cal_i)
        m=RandomForestRegressor(n_estimators=400,min_samples_leaf=5,n_jobs=-1,random_state=seed)
        m.fit(Xtr,ly[tr])
        p_c=np.log1p(m.predict(Xc)); p_t=np.log1p(m.predict(Xt)); p_ci=np.log1p(m.predict(Xci))
        s_c=np.abs(p_c-ly[cal]); s_ci=np.abs(p_ci-ly[cal_i]); s_t=np.abs(p_t-ly[te])
        q=np.quantile(s_c,min(1,(1-ALPHA)*(1+1/len(s_c))))
        cov=np.mean(s_t<=q)
        d,thr=di(Xtr,Xt,m.feature_importances_)
        rows.append(dict(seed=seed,country=c,n=len(te),gap=abs(cov-ALPHA-0+ (0)),
                         cov=cov, gap_signed=(1-ALPHA)-cov,
                         di_med=np.median(d), outAOA=float(np.mean(d>thr)),
                         W1_pred=wasserstein_distance(p_c,p_t),          # LABEL-FREE
                         W1_score=wasserstein_distance(s_c,s_t),         # oracle
                         shift_ratio=s_t.mean()/s_c.mean()))             # oracle
R=pd.DataFrame(rows)
print(R.round(3).to_string(index=False))
print("\n=== |signed coverage gap| correlations (n=%d fold-seeds) ==="%len(R))
G=R.gap_signed.abs()
for v in ["di_med","outAOA","W1_pred","W1_score","shift_ratio"]:
    r,p=spearmanr(R[v],G)
    print(f"{v:12s} spearman={r:+.3f}  p={p:.4f}")
print("\n=== per-country mean |gap| across seeds ===")
print(R.groupby('country').agg(n=('n','first'),mean_gap=('gap_signed',lambda s: s.abs().mean()),
      min_cov=('cov','min'),max_cov=('cov','max')).round(3))
print("\nmean |gap| pooled (all folds/seeds) = %.3f ; worst = %.3f"%(G.mean(),G.max()))
R.to_csv("diag_label_free.csv",index=False)
