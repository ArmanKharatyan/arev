"""ESA WorldCover land cover around every plant (optional; not yet used by the loss model)."""
import pandas as pd
from tqdm import tqdm

from arev import config as c
from arev.land_cover import land_cover

plants = pd.read_csv(c.PLANTS_FILE)
points = plants[["Latitude", "Longitude"]].itertuples(index=False)
cover = pd.DataFrame([land_cover(lat, lon) for lat, lon in tqdm(points, total=len(plants))])
cover.insert(0, "Plant Id", plants["Plant Id"])
cover.to_csv(c.LAND_COVER_FILE, index=False)
