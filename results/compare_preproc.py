"""Why does leave-one-country-out R2 differ from the earlier pilot?

Pilot used ONE global median imputation over the whole panel before splitting.
The package imputes inside each fold and adds missingness flags. This isolates
which choice moves the number.
"""
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from agroyield_adapt.schema import load_panel, build_matrix
from agroyield_adapt.checks.splits import r2_score, _prepare_fold

df = load_panel("One_Acre_Fund_MEL_maize_survey_data_2016-2022.csv")
X, y, ly = build_matrix(df)
groups = df.country.values
folds = list(GroupKFold(7).split(X, ly, groups))

def run(global_impute, add_flags, label):
    Xg = X.fillna(X.median(numeric_only=True)).fillna(0.0) if global_impute else X
    pred = np.zeros(len(df))
    for tr, te in folds:
        if global_impute:
            Xtr, Xte = Xg.iloc[tr], Xg.iloc[te]
        else:
            Xtr, Xte = _prepare_fold(X, tr, te)
            if not add_flags:
                Xtr = Xtr[[c for c in Xtr.columns if not c.endswith("_isna")]]
                Xte = Xte[[c for c in Xte.columns if not c.endswith("_isna")]]
        m = RandomForestRegressor(n_estimators=250, min_samples_leaf=5,
                                  n_jobs=-1, random_state=0).fit(Xtr, ly[tr])
        pred[te] = m.predict(Xte)
    rmse = float(np.sqrt(np.mean((np.expm1(ly) - np.expm1(pred)) ** 2)))
    print(f"{label:44s} R2(log)={r2_score(ly, pred):+7.3f}  RMSE={rmse:6.0f} kg/ha")

run(True,  False, "global median impute (old pilot style)")
run(False, False, "fold-internal impute, no missingness flags")
run(False, True,  "fold-internal impute + missingness flags (package)")
