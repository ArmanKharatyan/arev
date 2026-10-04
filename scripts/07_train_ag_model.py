"""Agricultural potential: learn long-term US county wheat yield from climate, predict for the candidate sites.

Needs a free USDA NASS API key in the NASS_KEY environment variable.
"""
import os
from functools import partial

import pandas as pd
import requests
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold, cross_val_predict

from arev import config as c
from arev.nasa import add_cells, climatology, fetch_cells

CROP = "WHEAT"
YEARS_FROM = 2015                # average yields over YEARS_FROM..latest
MIN_YEARS = 3                    # counties need this many years for a stable average
BU_ACRE_TO_T_HA = 0.0673         # wheat: 60 lb/bu
FEATURES = c.AG_FEATURES

# %% target: long-term average county yield
r = requests.get("https://quickstats.nass.usda.gov/api/api_GET/", params={
    "key": os.environ["NASS_KEY"], "format": "JSON", "agg_level_desc": "COUNTY", "source_desc": "SURVEY",
    "short_desc": f"{CROP} - YIELD, MEASURED IN BU / ACRE", "year__GE": YEARS_FROM,
})
r.raise_for_status()
nass = pd.DataFrame(r.json()["data"])
nass = nass[nass["county_code"] != "998"]                                # 998 = "other counties combined"
nass["yield_bu_acre"] = pd.to_numeric(nass["Value"].str.replace(",", ""), errors="coerce")
nass["GEOID"] = nass["state_fips_code"].str.zfill(2) + nass["county_code"].str.zfill(3)
counties = nass.groupby("GEOID").agg(
    yield_bu_acre=("yield_bu_acre", "mean"), n_years=("year", "nunique"), state=("state_alpha", "first")
).reset_index()
counties = counties[counties["n_years"] >= MIN_YEARS]

gaz = pd.read_csv(c.GAZETTEER_FILE, sep="\t", dtype={"GEOID": str})
gaz.columns = gaz.columns.str.strip()                                    # last header has trailing spaces
counties = counties.merge(gaz[["GEOID", "NAME", "INTPTLAT", "INTPTLONG"]], on="GEOID")
counties = add_cells(counties.rename(columns={"INTPTLAT": "Latitude", "INTPTLONG": "Longitude"}))

# %% long-term climate per grid cell
fetch = partial(climatology, params=FEATURES)
data = fetch_cells(counties, fetch, cache=c.AG_WEATHER_CACHE)
data = data.dropna(subset=FEATURES + ["yield_bu_acre"]).reset_index(drop=True)

# %% models, validated on unseen states
X, y = data[FEATURES], data["yield_bu_acre"]
models = {
    "linear": LinearRegression(),
    "boosting": HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=300, random_state=0),
}
predictions = {name: cross_val_predict(m, X, y, groups=data["state"], cv=GroupKFold(n_splits=5)) for name, m in models.items()}
scores = pd.DataFrame({name: {"MAE": mean_absolute_error(y, p), "R2": r2_score(y, p)} for name, p in predictions.items()}).T
scores.loc["baseline_median"] = [mean_absolute_error(y, [y.median()] * len(y)), 0.0]
final = models["boosting"].fit(X, y)

# %% predict for the candidate sites
sites = add_cells(pd.DataFrame(c.SITES, index=["Latitude", "Longitude"]).T.rename_axis("site").reset_index())
sites = fetch_cells(sites, fetch)
sites["yield_bu_acre"] = final.predict(sites[FEATURES])
sites["yield_t_ha"] = sites["yield_bu_acre"] * BU_ACRE_TO_T_HA
sites["percentile_vs_us"] = sites["yield_bu_acre"].apply(lambda v: (y < v).mean() * 100)   # 50 = typical US county

lo, hi = X.min(), X.max()
sites["outside_training_range"] = sites[FEATURES].apply(
    lambda row: ", ".join(f for f in FEATURES if not lo[f] <= row[f] <= hi[f]), axis=1
)

data["predicted_yield"] = predictions["boosting"]
for name, table in {"scores": scores, "data": data, "sites": sites}.items():
    table.to_csv(c.RESULTS / f"ag_model_{name}.csv", index=name != "sites")
