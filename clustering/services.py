"""Data import + clustering pipeline (kept out of views so it is testable and reusable)."""
import csv, io
import numpy as np
import pandas as pd
from django.db import transaction
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from .models import (INDICATORS, INDICATOR_FIELDS, ClusterAssignment, ClusterRun, County)

MIN_K, MAX_K = 2, 8


# ---------- import ----------
class ImportErrorList(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("; ".join(errors[:5]))


def import_counties_csv(file_obj):
    """Validate then upsert counties. Columns: code,name,[region],[is_asal],<indicators>,[source].
    All-or-nothing: any row error aborts the import and returns every error found."""
    text = file_obj.read()
    text = text.decode("utf-8-sig") if isinstance(text, bytes) else text
    reader = csv.DictReader(io.StringIO(text))
    cols = {c.strip().lower() for c in (reader.fieldnames or [])}
    missing = {"code", "name"} - cols
    if missing:
        raise ImportErrorList([f"Missing required column(s): {', '.join(sorted(missing))}"])
    errors, rows = [], []
    for n, raw in enumerate(reader, start=2):
        row = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
        try:
            code = int(row["code"])
            if not 1 <= code <= 47:
                raise ValueError("county code must be 1-47")
            data = {"code": code, "name": row["name"]}
            if not row["name"]:
                raise ValueError("name is empty")
            for f in INDICATOR_FIELDS:
                val = row.get(f, "")
                if val == "":
                    data[f] = None
                    continue
                num = float(val)
                if not 0 <= num <= 100:
                    raise ValueError(f"{f}={num} outside 0-100")
                data[f] = num
            data["region"] = row.get("region", "")
            data["is_asal"] = row.get("is_asal", "").lower() in {"1", "true", "yes", "y"}
            data["source"] = row.get("source", "")
            rows.append(data)
        except (ValueError, KeyError) as e:
            errors.append(f"Row {n}: {e}")
    if errors:
        raise ImportErrorList(errors)
    with transaction.atomic():
        for d in rows:
            County.objects.update_or_create(code=d.pop("code"), defaults=d)
    return len(rows)


# ---------- pipeline ----------
def load_frame():
    qs = County.objects.all().values("id", "name", *INDICATOR_FIELDS)
    df = pd.DataFrame(list(qs))
    return df


def prepare(df):
    """Drop indicators that are entirely empty, median-impute the rest, z-score scale."""
    feats = [f for f in INDICATOR_FIELDS if df[f].notna().any()]
    if len(feats) < 2:
        raise ValueError("Need at least two populated indicators to cluster.")
    X = df[feats].copy()
    imputed = int(X.isna().sum().sum())
    X = X.fillna(X.median())
    scaled = StandardScaler().fit_transform(X)
    return feats, scaled, imputed


def k_diagnostics(X, kmin=MIN_K, kmax=MAX_K):
    kmax = min(kmax, len(X) - 1)
    ks, inertia, sil = [], [], []
    for k in range(kmin, kmax + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        ks.append(k); inertia.append(float(km.inertia_)); sil.append(float(silhouette_score(X, km.labels_)))
    return {"k": ks, "inertia": inertia, "silhouette": sil}


def suggest_k(diag):
    return diag["k"][int(np.argmax(diag["silhouette"]))]


def fit_labels(X, algorithm, k):
    if algorithm == "kmeans":
        return KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)
    return AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(X)


def _need_score(df, feats, labels):
    """Composite 'access score' per cluster: mean z-score of indicators, sign-flipped when lower is better."""
    sign = {f: (1 if hb else -1) for f, _, hb in INDICATORS}
    z = (df[feats] - df[feats].mean()) / df[feats].std(ddof=0).replace(0, 1)
    z = z.fillna(0)
    composite = sum(z[f] * sign[f] for f in feats) / len(feats)
    return composite.groupby(labels).mean()


NAME_SETS = {2: ["High-need", "Well-served"],
             3: ["High-need", "Transitional", "Well-served"],
             4: ["Critical-need", "High-need", "Transitional", "Well-served"]}

def tier_names(k):
    if k in NAME_SETS:
        return NAME_SETS[k]
    return [f"Tier {i} ({'lowest' if i == 1 else 'highest' if i == k else 'mid'} access)" for i in range(1, k + 1)]


@transaction.atomic
def run_clustering(algorithm="kmeans", k=None, user=None):
    df = load_frame()
    if len(df) < 6:
        raise ValueError("Load county data first (at least 6 counties required).")
    feats, X, imputed = prepare(df)
    diag = k_diagnostics(X)
    k = k or suggest_k(diag)
    labels = fit_labels(X, algorithm, k)

    # re-number clusters 0..k-1 from lowest to highest sanitation access so labels are stable
    score = _need_score(df, feats, labels).sort_values()
    remap = {old: new for new, old in enumerate(score.index)}
    labels = np.array([remap[l] for l in labels])
    names = tier_names(k)

    pca = PCA(n_components=2, random_state=42).fit(X)
    coords = pca.transform(X)

    profiles = []
    for c in range(k):
        mask = labels == c
        prof = {"cluster": c, "label": names[c], "n": int(mask.sum()),
                "counties": sorted(df.loc[mask, "name"]),
                "means": {f: round(float(df.loc[mask, f].mean()), 1) for f in feats}}
        profiles.append(prof)

    run = ClusterRun.objects.create(
        algorithm=algorithm, n_clusters=k,
        silhouette=float(silhouette_score(X, labels)), davies_bouldin=float(davies_bouldin_score(X, labels)),
        explained_variance=[round(float(v), 4) for v in pca.explained_variance_ratio_],
        k_diagnostics={**diag, "suggested_k": suggest_k(diag), "features": feats, "imputed_cells": imputed},
        profiles=profiles, created_by=user if getattr(user, "is_authenticated", False) else None)
    ClusterAssignment.objects.bulk_create([
        ClusterAssignment(run=run, county_id=int(df.iloc[i]["id"]), cluster=int(labels[i]), label=names[labels[i]],
                          pc1=float(coords[i, 0]), pc2=float(coords[i, 1])) for i in range(len(df))])
    return run
