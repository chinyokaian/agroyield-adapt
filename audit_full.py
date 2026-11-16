import pandas as pd, numpy as np, sys
df = pd.read_csv("One_Acre_Fund_MEL_maize_survey_data_2016-2022.csv", low_memory=False)
out=[]
P=out.append
P(f"shape {df.shape}")
# find country/year-ish columns
cand=[c for c in df.columns if any(k in c.lower() for k in ["country","nation","year","season","site","region","zone","district","town","stratum","strat"])]
P("cand cols: "+repr(cand))
for c in cand:
    nu=df[c].nunique(dropna=True)
    P(f"\n== {c}  nunique={nu} missing={df[c].isna().mean():.3f}")
    if nu<=15:
        P(str(df[c].value_counts(dropna=False).to_dict()))
    else:
        P(str(df[c].value_counts(dropna=False).head(12).to_dict()))
# yield-ish
for c in df.columns:
    if "yield" in c.lower() or "kg" in c.lower():
        s=pd.to_numeric(df[c],errors="coerce")
        P(f"\nYIELDCOL {c} n={s.notna().sum()} median={s.median()} min={s.min()} max={s.max()}")
# per country-year counts if country exists
for cc in [c for c in df.columns if "countr" in c.lower()]:
    for yc in [c for c in df.columns if c.lower() in ("year","yr","season_year")]:
        P(f"\n=== counts by {cc} x {yc}")
        P(str(pd.crosstab(df[cc],df[yc],dropna=False)))
open("audit_full.txt","w",encoding="utf-8").write("\n".join(out))
print("ok")
