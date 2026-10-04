# Data

`raw/` holds downloads, `processed/` holds files the pipeline writes. Neither is committed.

## Files to put in `data/raw/`

| File | Source | What it gives |
|---|---|---|
| `EIA923_Schedules_2_3_4_5_M_12_2025_Final.xlsx` | [EIA-923](https://www.eia.gov/electricity/data/eia923/), 2025 ZIP | Annual net generation per plant |
| `2___Plant_Y2025.xlsx` | [EIA-860](https://www.eia.gov/electricity/data/eia860/), 2025 ZIP | Plant latitude and longitude |
| `3_3_Solar_Y2025.xlsx` | Same EIA-860 ZIP | Solar capacity (MW) and tracking type |
| `2024_Gaz_counties_national.txt` | [Census Gazetteer files](https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html), Counties | County centre points (only for `07_train_ag_model.py`) |

For a different year, change `YEAR` in `arev/config.py`; file names follow it. If EIA moves the header row in a new release, adjust `EIA923_SKIPROWS` / `EIA860_SKIPROWS`.

## Data fetched by API (no download needed)

- **NASA POWER**: annual and long-term weather per 0.5° x 0.625° grid cell. Cached in `processed/` after the first run; delete the cache file to refetch.
- **PVGIS** (EU JRC): typical meteorological year per site.
- **ESA WorldCover** via Microsoft Planetary Computer: land cover around each plant.
- **USDA NASS Quick Stats**: county crop yields. Needs a free key: <https://quickstats.nass.usda.gov/api>.
