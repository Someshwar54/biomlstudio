# streaming tabular and fasta + imbalance handling
import os, pandas as pd, numpy as np
try:
    from imblearn.over_sampling import SMOTE
    _HAS_SMOTE = True
except Exception:
    _HAS_SMOTE = False

def stream_csv(path, chunksize=1000):
    for chunk in pd.read_csv(path, chunksize=chunksize):
        yield chunk

def fasta_generator(path):
    name=None; seq=[]
    with open(path) as f:
        for line in f:
            line=line.strip()
            if line.startswith(">"):
                if name:
                    yield name, "".join(seq)
                name=line[1:]; seq=[]
            else:
                seq.append(line)
    if name:
        yield name, "".join(seq)

def preprocess_tabular(df, target_col='target'):
    df = df.copy()
    # simple impute mean
    for c in df.columns:
        if df[c].dtype.kind in 'biufc':
            df[c].fillna(df[c].mean(), inplace=True)
    y = df[target_col].values
    X = df.drop(columns=[target_col]).values
    # simple scale
    X = (X - X.mean(axis=0)) / (X.std(axis=0)+1e-6)
    return X, y

def balance_dataset(X, y):
    if _HAS_SMOTE:
        sm = SMOTE()
        Xb, yb = sm.fit_resample(X, y)
        return Xb, yb
    # fallback: simple random oversample minority
    classes, counts = np.unique(y, return_counts=True)
    if len(classes)<=1: return X,y
    maxc = counts.max()
    Xlist=[]; ylist=[]
    for cls in classes:
        Xi = X[y==cls]; yi = y[y==cls]
        reps = int(np.ceil(maxc / len(yi)))
        Xlist.append(np.tile(Xi, (reps,1))[:maxc])
        ylist.append(np.tile(yi, reps)[:maxc])
    Xb = np.vstack(Xlist); yb = np.concatenate(ylist)
    # shuffle
    idx = np.random.permutation(len(yb))
    return Xb[idx], yb[idx]