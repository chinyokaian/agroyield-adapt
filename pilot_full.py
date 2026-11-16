import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import NearestNeighbors
from scipy.stats import spearmanr, wasserstein_distance
np.random.seed(0)

df = pd.read_csv("One_Acre_Fund_MEL_maize_survey_data_2016-2022.csv", low_memory=False)

def to_bin(s):
    if s.dtype == bool: return s.astype(float)
    return s.astype(str).str.upper().map({'TRUE':1.0,'FALSE':0.0,'1':1.0,'0':0.0,'YES':1.0,'NO':0.0})

NUM = ['avg_season_gdd','avg_season_ai','avg_season_tavg','season_prec','season_prec_1',
       'season_prec_2','season_prec_3','elev','twi','soil_rzpawhc','soil_clay','soil_pH',
       'soil_orgC','soil_ECEC','N_kg_ha','P_kg_ha','K_kg_ha','lime_kg_ha','pl_m2',
       'row_spacing','plant_doy','plant_date_dev','hyb_mat']
BIN = ['hybrid','compost','weeding','pesticide','fert_in_hole','disease','pest','water_excess']

X = df[NUM].astype(float).copy()
for c in BIN: X[c] = to_bin(df[c]).fillna(0)
feat = list(X.columns)
y = df['yield_kg_ha'].astype(float).values
ly = np.log1p(y)

print("=== QC ===")
print("n=",len(df)," zeros in yield:",int((y==0).sum()), " (pct %.3f%%)"%(100*(y==0).mean()))
dup = df.duplicated(subset=['lon','lat','year'], keep=False)
print("rows sharing (lon,lat,year) with another row:",int(dup.sum()), "unique coord-year:", df.groupby(['lon','lat','year']).ngroups)
print("N heaping: exactly 112 kg/ha =", int((df.N_kg_ha==112).sum()), "top5 N values:", df.N_kg_ha.value_counts().head(5).to_dict())
print("\n=== yield by country ===")
print(df.groupby('country')['yield_kg_ha'].describe()[['count','mean','50%','std','min','max']].round(1))
print("\n=== median feature value by country (transport check) ===")
key=['season_prec','avg_season_tavg','avg_season_ai','soil_orgC','N_kg_ha','pl_m2','elev']
print(df.groupby('country')[key].median().round(2))
print("\n=== missingness by country for soil block ===")
print(df.groupby('country')['soil_clay'].apply(lambda s: round(100*s.isna().mean(),1)).to_dict())

def prep_fold(tr_idx, te_idx):
    Xtr = X.iloc[tr_idx].copy(); Xte = X.iloc[te_idx].copy()
    for c in NUM:
        med = Xtr[c].median()
        Xtr[c+'_isna'] = Xtr[c].isna().astype(float); Xte[c+'_isna'] = Xte[c].isna().astype(float)
        Xtr[c] = Xtr[c].fillna(med).fillna(0); Xte[c] = Xte[c].fillna(med).fillna(0)
    return Xtr, Xte

def di(Xtr, Xte, imp):
    mu, sd = Xtr.mean(), Xtr.std().replace(0,1)
    A = ((Xtr-mu)/sd).values; B = ((Xte-mu)/sd).values
    w = np.sqrt(np.asarray(imp)/np.asarray(imp).sum()*len(imp))
    nn = NearestNeighbors(n_neighbors=1).fit(A*w)
    d,_ = nn.kneighbors(B*w)
    # threshold = 0.95 quantile of train-to-train NN distance
    dt,_ = NearestNeighbors(n_neighbors=2).fit(A*w).kneighbors(A*w)
    thr = np.quantile(dt[:,1], 0.95)
    return d[:,0], thr

ALPHA = 0.10
countries = sorted(df.country.unique())
rows=[]; gaps=[]; dis=[]
for c in countries:
    te_all = np.where(df.country.values==c)[0]
    tr_all = np.where(df.country.values!=c)[0]
    rng = np.random.default_rng(7)
    te_all = rng.permutation(te_all)
    te, cal_i = te_all[:len(te_all)//2], te_all[len(te_all)//2:]
    tr_all = rng.permutation(tr_all)
    ncal = max(len(tr_all)//3, 200)
    cal, tr = tr_all[:ncal], tr_all[ncal:]
    Xtr, Xc = prep_fold(tr, cal)
    _, Xt = prep_fold(tr, te)
    _, Xci = prep_fold(tr, cal_i)
    m = RandomForestRegressor(n_estimators=400, min_samples_leaf=5, n_jobs=-1, random_state=0)
    m.fit(Xtr, ly[tr])
    s_c  = np.abs(np.log1p(m.predict(Xc)) - ly[cal])
    s_ci = np.abs(np.log1p(m.predict(Xci)) - ly[cal_i])
    q_pool = np.quantile(s_c, min(1, (1-ALPHA)*(1+1/len(s_c))))
    q_own  = np.quantile(s_ci, min(1, (1-ALPHA)*(1+1/len(s_ci))))
    pr = m.predict(Xt); yt = y[te]
    def ev(q):
        lo = np.expm1(np.log1p(pr)-q); hi = np.expm1(np.log1p(pr)+q)
        cov = np.mean((yt>=lo)&(yt<=hi)); return cov, np.median(hi-lo)
    cov_p, w_p = ev(q_pool); cov_o, w_o = ev(q_own)
    d, thr = di(Xtr, Xt, m.feature_importances_)
    w1 = wasserstein_distance(s_c, np.abs(np.log1p(pr)-ly[te]))
    out = float(np.mean(d>thr))
    rows.append(dict(country=c, n_test=len(te), cov_pooled=cov_p, cov_own=cov_o,
                     gap=abs(cov_p-1+ALPHA), w_pooled=w_p, w_own=w_o,
                     di_med=float(np.median(d)), frac_outAOA=out, score_W1=w1))
    print(f"{c:9s} n={len(te):5d} cov_pooled={cov_p:.3f} cov_own={cov_o:.3f} "
          f"w_pooled={w_p:7.0f} w_own={w_o:7.0f} DI={np.median(d):.2f} outAOA={out:.2f} W1={w1:.3f}")

R = pd.DataFrame(rows)
print("\n=== summary ===")
print(R.round(3).to_string(index=False))
print(f"\nmean |gap| pooled = {R.gap.mean():.3f}   mean |cov_own - 0.9| = {abs(R.cov_own-0.9).mean():.3f}")
print(f"width inflation for own-country calibration: {(R.w_own/R.w_pooled).median():.2f}x median")
from scipy.stats import spearmanr
print(f"Spearman(DI_med, gap) = {spearmanr(R.di_med, R.gap)[0]:.3f}  p={spearmanr(R.di_med, R.gap)[1]:.3f}")
print(f"Spearman(frac_outAOA, gap) = {spearmanr(R.frac_outAOA, R.gap)[0]:.3f}  p={spearmanr(R.frac_outAOA, R.gap)[1]:.3f}")
print(f"Spearman(score_W1, gap) = {spearmanr(R.score_W1, R.gap)[0]:.3f}  p={spearmanr(R.score_W1, R.gap)[1]:.3f}")
R.to_csv("pilot_full_results.csv", index=False)
