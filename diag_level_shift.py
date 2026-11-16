import numpy as np, pandas as pd
from scipy.stats import spearmanr, pearsonr
exec(open("pilot_full.py").read().split("ALPHA = 0.10")[0])

R=pd.read_csv("diag_label_free.csv")
g=R.groupby('country').agg(gap_signed=('gap_signed','mean'), cov=('cov','mean'),
                           di_med=('di_med','mean'), W1_pred=('W1_pred','mean')).reset_index()
st=df.groupby('country').agg(med_y=('yield_kg_ha','median'), mean_logy=('yield_kg_ha',lambda s: np.log1p(s).mean()),
                             sd_logy=('yield_kg_ha',lambda s: np.log1p(s).std())).reset_index()
M=g.merge(st,on='country')
pool_logy=np.log1p(df.yield_kg_ha).mean(); pool_sd=np.log1p(df.yield_kg_ha).std()
M['level_shift']=(M.mean_logy-pool_logy)/pool_sd     # signed, in SD units vs pooled calibration pool
print(M.round(3).to_string(index=False))
print("\n=== does the SIGNED coverage gap track the yield-level shift? ===")
for v in ['med_y','mean_logy','level_shift','di_med','W1_pred']:
    r,p=spearmanr(M[v],M.gap_signed); print(f"  spearman({v:12s}, signed gap) = {r:+.3f}  p={p:.4f}")
print("\n=== ABSOLUTE gap (what the auditor must predict) ===")
M['absgap']=M.gap_signed.abs()
for v in ['level_shift','med_y','di_med','W1_pred','sd_logy']:
    r,p=spearmanr(M[v],M.absgap); print(f"  spearman({v:12s}, |gap|) = {r:+.3f}  p={p:.4f}")
print("\n=== per-country predictor-block shift (standardised mean diff vs pooled) ===")
CLIM=['avg_season_gdd','avg_season_ai','avg_season_tavg','season_prec','season_prec_1','season_prec_2','season_prec_3','elev','twi']
SOIL=['soil_rzpawhc','soil_clay','soil_pH','soil_orgC','soil_ECEC']
MGMT=['N_kg_ha','P_kg_ha','K_kg_ha','lime_kg_ha','pl_m2','row_spacing','plant_doy','plant_date_dev','hyb_mat']
out=[]
for c in M.country:
    d=df[df.country==c]
    row={'country':c}
    for name,cols in [('clim',CLIM),('soil',SOIL),('mgmt',MGMT)]:
        ds=[]
        for col in cols:
            a=pd.to_numeric(d[col],errors='coerce').dropna(); b=pd.to_numeric(df[col],errors='coerce').dropna()
            if len(a)<20 or b.std()==0: continue
            ds.append(abs(a.mean()-b.mean())/b.std())
        row[name]=np.mean(ds) if ds else np.nan
    out.append(row)
B=pd.DataFrame(out).merge(M[['country','absgap','gap_signed']],on='country')
print(B.round(3).to_string(index=False))
for v in ['clim','soil','mgmt']:
    r,p=spearmanr(B[v],B.absgap); print(f"  spearman({v} block shift, |gap|) = {r:+.3f} p={p:.4f}")
B.to_csv("level_shift.csv",index=False); M.to_csv("level_shift_meta.csv",index=False)
