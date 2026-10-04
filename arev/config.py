from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"

YEAR = 2025                      # EIA generation year; NASA weather is fetched for the same year
N_PLANTS = 1000

# raw downloads (see data/README.md)
EIA923_FILE = RAW / f"EIA923_Schedules_2_3_4_5_M_12_{YEAR}_Final.xlsx"
EIA860_PLANT_FILE = RAW / f"2___Plant_Y{YEAR}.xlsx"
EIA860_SOLAR_FILE = RAW / f"3_3_Solar_Y{YEAR}.xlsx"
GAZETTEER_FILE = RAW / "2024_Gaz_counties_national.txt"
EIA923_SKIPROWS = 5              # rows above the header in EIA-923 "Page 1"
EIA860_SKIPROWS = 1

# pipeline outputs
PLANTS_FILE = PROCESSED / f"eia_solar_pv_{YEAR}.csv"
WEATHER_CACHE = PROCESSED / f"nasa_cells_{YEAR}.csv"
PLANTS_WEATHER_FILE = PROCESSED / f"plants_weather_{YEAR}.csv"
LAND_COVER_FILE = PROCESSED / "plants_land_cover.csv"
AG_WEATHER_CACHE = PROCESSED / "nasa_ag_cells.csv"
LOSS_MODEL_FILE = RESULTS / "loss_model.joblib"

LOSS_FEATURES = [
    "ALLSKY_KT", "ALLSKY_SRF_ALB", "AOD_55", "CLOUD_AMT", "T2M", "T2M_MAX",
    "T2M_RANGE", "RH2M", "PRECTOTCORR", "WS10M", "tracking",
]
LOSS_NASA_PARAMS = [f for f in LOSS_FEATURES if f != "tracking"] + ["ALLSKY_SFC_SW_DWN"]

AG_FEATURES = [
    "T2M", "T2M_MAX", "T2M_MIN", "T2M_RANGE", "PRECTOTCORR", "RH2M",
    "WS2M", "ALLSKY_SFC_SW_DWN", "GWETROOT", "GWETTOP",
]

SITES = {                        # candidate sites in Armenia
    "Yerevan": (40.18, 44.51),
    "Gyumri": (40.79, 43.85),
    "Mets Masrik": (40.21, 45.76),
    "Sisian": (39.52, 46.03),
}
