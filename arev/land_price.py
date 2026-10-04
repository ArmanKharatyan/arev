"""Approximate agricultural land price in Armenia from coordinates.

price = FLOOR + accessibility x land cover multiplier x slope multiplier

Accessibility: price falls with distance from population centres as (DECAY_KM / (d + DECAY_KM)) ** DECAY_POWER,
scaled by (population / Yerevan population) ** POP_EXPONENT; the highest-priced centre wins. Meant for farmland and open land, not urban plots.
Calibrated to list.am asking prices for agricultural plots around Yerevan (Oct 2026):
about $25/m² at 8 km, $7-20/m² at 13-20 km, $3-4/m² at 35-40 km. Expect errors of up to a factor of 2.
"""
import numpy as np
import pandas as pd
import requests

ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"

CITIES = {                       # name: (lat, lon, population, approx.)
    "Yerevan": (40.179, 44.499, 1_090_000), "Gyumri": (40.789, 43.848, 112_000),
    "Vanadzor": (40.813, 44.488, 75_000), "Vagharshapat": (40.166, 44.293, 46_000),
    "Abovyan": (40.274, 44.626, 44_000), "Kapan": (39.208, 46.406, 42_000),
    "Hrazdan": (40.497, 44.766, 39_000), "Armavir": (40.155, 44.039, 28_000),
    "Artashat": (39.954, 44.551, 20_000), "Ararat": (39.831, 44.705, 20_000),
    "Ijevan": (40.876, 45.149, 20_000), "Goris": (39.511, 46.339, 20_000),
    "Charentsavan": (40.402, 44.645, 20_000), "Gavar": (40.359, 45.127, 19_000),
    "Sevan": (40.549, 44.949, 18_000), "Ashtarak": (40.299, 44.362, 18_000),
    "Masis": (40.066, 44.435, 18_000), "Dilijan": (40.742, 44.864, 15_000),
    "Sisian": (39.521, 46.032, 14_000), "Stepanavan": (41.009, 44.384, 12_000),
    "Spitak": (40.837, 44.268, 12_000), "Alaverdi": (41.098, 44.651, 12_000),
    "Martuni": (40.139, 45.307, 11_000), "Yeghegnadzor": (39.761, 45.333, 7_000),
}
CENTRE_PRICE = 141               # USD/m², scale of the decay curve (gives ~$25/m² at 8 km from Yerevan)
DECAY_KM = 5
DECAY_POWER = 1.8
POP_EXPONENT = 0.7               # how much smaller towns lift prices around them
FLOOR = 0.2                      # USD/m², remote land
COVER_MULTIPLIER = {             # relative to cropland, which the calibration plots were
    "cropland": 1.0, "built_up": 2.0, "grassland": 0.6, "shrubland": 0.5, "tree": 0.5, "bare": 0.4,
    "moss_lichen": 0.3, "snow_ice": 0.0, "water": 0.0, "wetland": 0.0, "mangroves": 0.0,
}
SLOPE_STEP_M = 100               # spacing of the elevation samples used for slope


def haversine_km(lat, lon, lat2, lon2):
    lat, lon, lat2, lon2 = map(np.radians, (lat, lon, lat2, lon2))
    a = np.sin((lat2 - lat) / 2) ** 2 + np.cos(lat) * np.cos(lat2) * np.sin((lon2 - lon) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def accessibility(lat, lon):
    """Price driven by the most valuable nearby population centre."""
    c = pd.DataFrame(CITIES, index=["lat", "lon", "pop"]).T
    km = haversine_km(lat, lon, c["lat"], c["lon"])
    price = CENTRE_PRICE * (c["pop"] / c["pop"].max()) ** POP_EXPONENT * (DECAY_KM / (km + DECAY_KM)) ** DECAY_POWER
    best = price.idxmax()
    return {"accessibility_usd_m2": price[best], "price_centre": best, "km_to_centre": km[best], "km_to_yerevan": km["Yerevan"]}


def terrain(lat, lon):
    """Elevation (m) and slope (degrees) from Copernicus DEM via Open-Meteo, one request of 5 points."""
    dlat = SLOPE_STEP_M / 111_320
    dlon = dlat / np.cos(np.radians(lat))
    lats = [lat, lat + dlat, lat - dlat, lat, lat]
    lons = [lon, lon, lon, lon + dlon, lon - dlon]
    r = requests.get(ELEVATION_URL, params={"latitude": ",".join(map(str, lats)), "longitude": ",".join(map(str, lons))})
    r.raise_for_status()
    z, n, s, e, w = r.json()["elevation"]
    grad = np.hypot((n - s) / (2 * SLOPE_STEP_M), (e - w) / (2 * SLOPE_STEP_M))
    return {"elevation_m": z, "slope_deg": np.degrees(np.arctan(grad))}


def estimate(lat, lon, cover_shares=None):
    """Land price estimate. cover_shares: land_cover() output; None treats the site as cropland."""
    out = {**accessibility(lat, lon), **terrain(lat, lon)}
    out["cover_multiplier"] = 1.0 if cover_shares is None else sum(
        cover_shares[f"share_{k}"] * m for k, m in COVER_MULTIPLIER.items())
    out["slope_multiplier"] = max(0.3, 1 - out["slope_deg"] / 30)
    out["price_usd_m2"] = FLOOR + out["accessibility_usd_m2"] * out["cover_multiplier"] * out["slope_multiplier"]
    out["low_usd_m2"], out["high_usd_m2"] = out["price_usd_m2"] / 2, out["price_usd_m2"] * 2
    return out
