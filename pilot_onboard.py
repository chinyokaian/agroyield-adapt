import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
exec(open("pilot_full.py").read().split("ALPHA = 0.10")[0])
ALPHA=0.10

def wquant(s, w, level):
    o=np.argsort(s); s=s[o]; w=w[o]; cw=np.cumsum(w)/w.sum()
    i=np.searchsorted(cw, level)
    return s[min(i, len(s)-1)]

rows=[]
for c in sorted(df.country.unique()):
    te_all=np.where(df.country.values==c)[0]; tr_all=np.where(df.country.values!=c)[0]
    rng=np.random.default_rng(0)
    te_all=rng.permutation(te_all); te,cal_i=te_all[:len(te_all)//2],te_all[len(te_all)//2:]
    tr_all=rng.permutation(tr_all); ncal=max(len(tr_all)//3,200)
    cal,tr=tr_all[:ncal],tr_all[ncal:]
    Xtr,Xc=prep_fold(tr,cal); _,Xt=prep_fold(tr,te); _,Xci=prep_fold(tr,cal_i)
    # prep_fold was fit on 'tr' medians; refit on union for a fair target-domain encoding
    Xall_tr, Xall_x = prep_fold(np.concatenate([tr,cal]), np.concatenate([te,cal_i]))
    m=RandomForestRegressor(n_estimators=400,min_samples_leaf=5,n_jobs=-1,random_state=0).fit(Xtr,ly[tr])
    s_c=np.abs(np.log1p(m.predict(Xc))-ly[cal]); s_t=np.abs(np.log1p(m.predict(Xt))-ly[te])
    s_ci=np.abs(np.log1p(m.predict(Xci))-ly[cal_i])
    # label-free density ratio: cal (source) vs target covariates (no labels used)
    A=Xall_tr.values; B=Xall_x.values
    sc=StandardScaler().fit(A); A=sc.transform(A); B=sc.transform(B)
    d=np.r_[np.zeros(len(A)),np.ones(len(B))]
    clf=LogisticRegression(max_iter=2000,C=0.05).fit(np.vstack([A,B]),d)
    p=clf.predict_proba(A)[:,1]; w=np.clip(p/(1-p+1e-9),1e-6,None)
    w=w/w.mean(); w=np.clip(w,0.1,10.0); w=w/w.sum()
    ess=1.0/np.sum(w**2)/len(w)   # ESS fraction
    q_pool=np.quantile(s_c,min(1,(1-ALPHA)*(1+1/len(s_c))))
    q_w=wquant(s_c,w,1-ALPHA)
    q_own=np.quantile(s_ci,min(1,(1-ALPHA)*(1+1/len(s_ci))))
    def cov(q): return float(np.mean(s_t<=q))
    rows.append(dict(country=c,n=len(te),cov_pooled=cov(q_pool),cov_weighted=cov(q_w),
                     cov_oracle=cov(q_own),q_pool=q_pool,q_w=q_w,q_own=q_own,ess=ess))
R=pd.DataFrame(rows)
print(R.round(3).to_string(index=False))
G=lambda col: (R[col]-0.9).abs()
print("\nmean |cov-0.9|:  pooled=%.3f  weighted=%.3f  oracle(own labels)=%.3f"%(G('cov_pooled').mean(),G('cov_weighted').mean(),G('cov_oracle').mean()))
print("worst |cov-0.9|: pooled=%.3f  weighted=%.3f  oracle=%.3f"%(G('cov_pooled').max(),G('cov_weighted').max(),G('cov_oracle').max()))
print("median ESS fraction (1.0 = weighting useless):", round(R.ess.median(),3))
print("median interval width ratio weighted/pooled:", round((R.q_w/R.q_pool).median(),3))
R.to_csv("pilot_onboard_results.csv",index=False)
