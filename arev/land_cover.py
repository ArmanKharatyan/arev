import numpy as np
import pandas as pd
import planetary_computer
import pystac_client
import rasterio
from rasterio.windows import from_bounds

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
CLASSES = {
    10: "tree", 20: "shrubland", 30: "grassland", 40: "cropland", 50: "built_up", 60: "bare",
    70: "snow_ice", 80: "water", 90: "wetland", 95: "mangroves", 100: "moss_lichen",
}

catalog = pystac_client.Client.open(STAC_URL, modifier=planetary_computer.sign_inplace)


def land_cover(lat, lon, radius_m=1000, year=2021):
    """ESA WorldCover class at the point and class shares in a square of +-radius_m around it."""
    dlat = radius_m / 111_320
    dlon = dlat / np.cos(np.radians(lat))
    bbox = (lon - dlon, lat - dlat, lon + dlon, lat + dlat)

    pixels, center = [], None
    for item in catalog.search(collections=["esa-worldcover"], bbox=bbox, datetime=str(year)).items():
        with rasterio.open(item.assets["map"].href) as src:   # a box near a tile edge spans several 3°x3° tiles
            pixels.append(src.read(1, window=from_bounds(*bbox, src.transform), boundless=True, fill_value=0).ravel())
            b = src.bounds
            if b.left <= lon < b.right and b.bottom <= lat < b.top:
                center = CLASSES[int(next(src.sample([(lon, lat)]))[0])]

    pixels = np.concatenate(pixels)
    shares = pd.Series(pixels[pixels > 0]).map(CLASSES).value_counts(normalize=True)
    shares = shares.reindex(CLASSES.values(), fill_value=0).add_prefix("share_")
    return {"center_class": center, **shares}
