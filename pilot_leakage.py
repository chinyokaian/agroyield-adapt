import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, GroupKFold
exec(open("pilot_full.py").read().split("ALPHA = 0.10")[0])

Xf = X.fillna(X.median(numeric_only=True)).fillna(0)
grp_xy = (df.lon.round(1).astype(str)+"_"+df.lat.round(1).astype(str)+"_"+df.year.astype(str)).values
grp_country = df.country.values

def r2(yy, pp): 
    ss=((yy-yy.mean())**2).sum(); return 1-((yy-pp)**2).sum()/ss

def run(splitter, groups, label):
    pred=np.zeros(len(df)); k=0
    for tr,te in splitter.split(Xf, ly, groups):
        m=RandomForestRegressor(n_estimators=250,min_samples_leaf=5,n_jobs=-1,random_state=0).fit(Xf.iloc[tr],ly[tr])
        pred[te]=m.predict(Xf.iloc[te]); k+=1
    rmse=np.sqrt(np.mean((np.expm1(ly)-np.expm1(pred))**2))
    print(f"{label:38s} folds={k}  R2(log)={r2(ly,pred):+.3f}  RMSE={rmse:7.0f} kg/ha")
    return r2(ly,pred)

print("rows",len(df)," clusters(coord0.1+year)",len(set(grp_xy))," countries",len(set(grp_country)))
print("\n=== same model, same features, three split designs ===")
a=run(KFold(5,shuffle=True,random_state=0), None, "random 5-fold (what many papers report)")
b=run(GroupKFold(5), grp_xy, "group 5-fold by coord(0.1deg)+year")
c=run(GroupKFold(7), grp_country, "leave-one-country-out (7 folds)")
print(f"\ninflation from ignoring spatial-temporal clusters: {a-b:+.3f} R2")
print(f"inflation from ignoring country structure        : {a-c:+.3f} R2")
dups=df.duplicated(subset=['lon','lat','year'],keep=False)
print(f"rows in duplicate coord-year clusters: {int(dups.sum())} ({100*dups.mean():.1f}%)")
