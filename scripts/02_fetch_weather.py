"""NASA POWER annual weather for every plant, one request per grid cell, cached."""
from functools import partial

import pandas as pd

from arev import config as c
from arev.nasa import add_cells, annual, fetch_cells

plants = add_cells(pd.read_csv(c.PLANTS_FILE))
fetch = partial(annual, params=c.LOSS_NASA_PARAMS, year=c.YEAR)
data = fetch_cells(plants, fetch, cache=c.WEATHER_CACHE)
data.to_csv(c.PLANTS_WEATHER_FILE, index=False)
