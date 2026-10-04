import time

import pandas as pd
import requests
from tqdm import tqdm

URL = "https://power.larc.nasa.gov/api/temporal/{temporal}/point"
PAUSE = 2                        # POWER allows ~30 requests per minute


def _get(temporal, lat, lon, params, community, **extra):
    r = requests.get(URL.format(temporal=temporal), params={
        "parameters": ",".join(params), "community": community,
        "latitude": lat, "longitude": lon, "format": "JSON", **extra,
    })
    r.raise_for_status()
    time.sleep(PAUSE)
    return r.json()["properties"]["parameter"]


def annual(lat, lon, params, year, community="RE"):
    """Values for one year. The monthly endpoint is the only one with per-year values; key "YYYY13" is the annual one."""
    data = _get("monthly", lat, lon, params, community, start=year, end=year)
    return {p: v[f"{year}13"] for p, v in data.items()}


def climatology(lat, lon, params, community="AG"):
    """Long-term annual averages ("ANN")."""
    return {p: v["ANN"] for p, v in _get("climatology", lat, lon, params, community).items()}


def add_cells(df):
    """Snap points to the POWER grid (0.5° lat x 0.625° lon); points in one cell get identical data."""
    df["lat_cell"] = (df["Latitude"] / 0.5).round() * 0.5
    df["lon_cell"] = (df["Longitude"] / 0.625).round() * 0.625
    return df


def fetch_cells(df, fetch, cache=None):
    """Attach weather to every row of df, requesting each grid cell once. fetch(lat, lon) -> dict."""
    if cache is not None and cache.exists():
        weather = pd.read_csv(cache)
    else:
        cells = df[["lat_cell", "lon_cell"]].drop_duplicates().reset_index(drop=True)
        weather = pd.concat([cells, pd.DataFrame([fetch(lat, lon) for lat, lon in tqdm(cells.itertuples(index=False), total=len(cells))])], axis=1)
        weather = weather.replace(-999, float("nan"))
        if cache is not None:
            weather.to_csv(cache, index=False)
    return df.merge(weather, on=["lat_cell", "lon_cell"], how="left")
