"""Approximate land price and land cost of a solar plant for the candidate sites in config.SITES."""
import pandas as pd

from arev import config as c
from arev.land_price import estimate

USE_LAND_COVER = True            # False skips Planetary Computer and treats every site as cropland
PLANT_MW = 1

if USE_LAND_COVER:
    from arev.land_cover import land_cover

rows = []
for name, (lat, lon) in c.SITES.items():
    cover = land_cover(lat, lon) if USE_LAND_COVER else None
    rows.append({"site": name, "lat": lat, "lon": lon, **estimate(lat, lon, cover),
                 "center_class": cover["center_class"] if USE_LAND_COVER else None})

prices = pd.DataFrame(rows)
prices["price_amd_m2"] = prices["price_usd_m2"] * c.USD_AMD
prices["price_usd_ha"] = prices["price_usd_m2"] * 10_000
prices["land_cost_usd"] = prices["price_usd_ha"] * c.HA_PER_MW * PLANT_MW
prices.to_csv(c.RESULTS / "land_price.csv", index=False)
