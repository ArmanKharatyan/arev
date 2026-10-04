"""PVGIS typical-year climate summary (annual and monthly) for the candidate sites."""
import pandas as pd

from arev import config as c
from arev.pvgis import tmy

annual_rows, monthly_tables = [], {}
for name, (lat, lon) in c.SITES.items():
    hourly = tmy(lat, lon)
    means = hourly.drop(columns="month").mean().add_suffix("_mean")
    irradiation = (hourly[["G(h)", "Gb(n)", "Gd(h)"]].sum() / 1000).add_suffix("_kwh_m2_yr")
    annual_rows.append({"site": name, "lat": lat, "lon": lon, **means, **irradiation})
    monthly_tables[name] = hourly.groupby("month").mean()

pd.DataFrame(annual_rows).to_csv(c.RESULTS / "site_climate_annual.csv", index=False)
pd.concat(monthly_tables, names=["site"]).to_csv(c.RESULTS / "site_climate_monthly.csv")
