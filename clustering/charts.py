"""Plotly figures returned as JSON strings for the templates."""
import json
import plotly.graph_objects as go
import plotly.express as px
from django.conf import settings

COLORS = ["#c0392b", "#e67e22", "#f1c40f", "#27ae60", "#2980b9", "#8e44ad", "#16a085", "#7f8c8d"]
_LAYOUT = dict(margin=dict(l=40, r=20, t=40, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")


def _json(fig):
    return fig.to_json()


def pca_scatter(run):
    fig = go.Figure()
    rows = list(run.assignments.select_related("county"))
    for c in sorted({r.cluster for r in rows}):
        sub = [r for r in rows if r.cluster == c]
        fig.add_trace(go.Scatter(x=[r.pc1 for r in sub], y=[r.pc2 for r in sub], mode="markers+text",
                                 text=[r.county.name for r in sub], textposition="top center", textfont_size=9,
                                 name=sub[0].label, marker=dict(size=11, color=COLORS[c % len(COLORS)])))
    ev = run.explained_variance
    fig.update_layout(title="PCA projection of counties", xaxis_title=f"PC1 ({ev[0]:.0%} variance)",
                      yaxis_title=f"PC2 ({ev[1]:.0%} variance)", **_LAYOUT)
    return _json(fig)


def k_selection(run):
    d = run.k_diagnostics
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["k"], y=d["inertia"], name="Inertia (elbow)", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=d["k"], y=d["silhouette"], name="Silhouette", mode="lines+markers", yaxis="y2"))
    fig.update_layout(title="Choosing k", xaxis_title="k", yaxis=dict(title="Inertia"),
                      yaxis2=dict(title="Silhouette", overlaying="y", side="right"),
                      legend=dict(orientation="h", y=-0.25), **_LAYOUT)
    return _json(fig)


def profile_heatmap(run):
    feats = run.k_diagnostics["features"]
    z = [[p["means"][f] for f in feats] for p in run.profiles]
    fig = go.Figure(go.Heatmap(z=z, x=feats, y=[p["label"] for p in run.profiles], colorscale="RdYlGn",
                               text=z, texttemplate="%{text}"))
    fig.update_layout(title="Cluster means by indicator", **_LAYOUT)
    return _json(fig)


def _norm(s):
    return "".join(ch for ch in s.lower() if ch.isalnum())


def choropleth(run):
    """County choropleth. Matches polygons by county code when the GeoJSON has one (COUNTY_COD etc.),
    otherwise by normalised name. Returns None when no GeoJSON file is present."""
    path = settings.COUNTY_GEOJSON
    if not path.exists():
        return None
    gj = json.loads(path.read_text(encoding="utf-8"))
    props = [f.get("properties") or {} for f in gj["features"]]
    code_key = next((k for k in ("COUNTY_COD", "county_code", "COUNTY_CODE", "CODE") if any(p.get(k) for p in props)), None)
    name_key = next((k for k in ("COUNTY_NAM", "county", "COUNTY", "name", "NAME_1") if any(p.get(k) for p in props)), None)
    if code_key is None and name_key is None:
        return None
    keep = []
    for f in gj["features"]:
        p = f.get("properties") or {}
        ident = p.get(code_key) if code_key else _norm(p.get(name_key) or "")
        if ident:                       # skips blank/placeholder polygons (e.g. code 0, no name)
            f["id"] = ident
            keep.append(f)
    gj["features"] = keep
    rows = list(run.assignments.select_related("county"))
    ids = [r.county.code if code_key else _norm(r.county.name) for r in rows]
    fig = px.choropleth(locations=ids, geojson=gj, color=[r.label for r in rows],
                        hover_name=[r.county.name for r in rows],
                        category_orders={"color": [p["label"] for p in run.profiles]},
                        color_discrete_sequence=COLORS)
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(title="Sanitation clusters across Kenya", legend_title="Cluster", **_LAYOUT)
    return _json(fig)