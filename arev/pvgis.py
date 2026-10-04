import pandas as pd
import requests

URL = "https://re.jrc.ec.europa.eu/api/v5_3/tmy"


def tmy(lat, lon):
    """Hourly Typical Meteorological Year from PVGIS, with a month column and without wind direction."""
    r = requests.get(URL, params={"lat": lat, "lon": lon, "outputformat": "json"})
    r.raise_for_status()
    df = pd.DataFrame(r.json()["outputs"]["tmy_hourly"])
    df["month"] = df["time(UTC)"].str[4:6].astype(int)
    return df.drop(columns=["time(UTC)", "WD10m"])     # wind direction is circular, an arithmetic mean is meaningless
