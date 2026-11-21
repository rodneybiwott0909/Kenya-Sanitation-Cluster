# Kenya County Sanitation Clustering (Django)

Capstone: group Kenya's 47 counties into sanitation-access tiers with K-Means and Hierarchical (Ward) clustering,
validate with PCA, silhouette and Davies-Bouldin, and explore results on a web dashboard.

Stack (same family as EduPath): Python 3.12, Django 5.0, PostgreSQL 16 (SQLite fallback), Bootstrap 5.3,
scikit-learn, pandas, Plotly.

## Setup
    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env          # set DB_NAME to use PostgreSQL; blank = SQLite
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py load_counties                      # 47 counties, codes, regions
    python manage.py load_counties --csv data/my_real_data.csv   # real KNBS/KDHS/JMP indicators
    python manage.py runserver

## Data
Fill `data/county_template.csv` with real indicators (0-100), then upload at /upload/ or use the command above.
`python manage.py seed_demo` loads SYNTHETIC values purely to test the pipeline. Never report results from it.
Indicators: improved sanitation, open defecation, improved water, handwashing facility, poverty rate, urban population.
Add or change indicators in `clustering/models.py` (INDICATORS list) plus a migration.

## Pipeline (clustering/services.py)
1. Median-impute gaps, z-score scale. 2. Elbow + silhouette for k = 2..8 (suggested k = best silhouette).
3. Fit K-Means or Ward. 4. Order clusters by a composite access score so labels are stable
(High-need / Transitional / Well-served for k=3). 5. PCA to 2D. 6. Store profiles and assignments.
CLI: `python manage.py run_clustering --algorithm hierarchical --k 3`

## Choropleth (stretch goal)
Put a county-boundary GeoJSON at `data/kenya_counties.geojson` (name property such as `county`, `COUNTY_NAM`, `NAME_1`).
The map appears automatically on run pages. County names are matched ignoring case/punctuation, so check that
spellings (e.g. Murang'a, Taita-Taveta) line up.

## Tests
    python manage.py test

## Mapping to the proposal
Weeks 1-2: models, import, county list, EDA in the notebook/dashboard. Week 3: services.py. Week 4: profiles and
exports. Week 5: dashboard (Django + Plotly replaces the optional Streamlit app).
# Kenya-Sanitation-Cluster
