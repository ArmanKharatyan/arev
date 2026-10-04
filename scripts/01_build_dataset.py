"""EIA solar PV plants: annual generation (EIA-923) + coordinates and capacity (EIA-860)."""
from arev import config as c
from arev.eia import load_capacity, load_coordinates, load_generation

gen = load_generation(c.EIA923_FILE, c.EIA923_SKIPROWS)
coords = load_coordinates(c.EIA860_PLANT_FILE, c.EIA860_SKIPROWS)
capacity = load_capacity(c.EIA860_SOLAR_FILE, c.EIA860_SKIPROWS)

plants = gen.join(coords, on="Plant Id", how="inner").join(capacity, on="Plant Id", how="inner").head(c.N_PLANTS)
plants.to_csv(c.PLANTS_FILE, index=False)
