"""Predict output per unit of sunlight and annual energy for the candidate sites in config.SITES."""
import joblib
import pandas as pd

from arev import config as c
from arev.nasa import annual

TRACKING = 0                     # 0 = fixed panels, 1 = tracker
CAPACITY_MW = 1
FEATURES = c.LOSS_FEATURES

model = joblib.load(c.LOSS_MODEL_FILE)
train = pd.read_csv(c.RESULTS / "loss_model_data.csv")

sites = pd.DataFrame({name: annual(lat, lon, c.LOSS_NASA_PARAMS, c.YEAR) for name, (lat, lon) in c.SITES.items()}).T
sites = sites.replace(-999, float("nan"))
sites["tracking"] = TRACKING

sites["yield_ratio"] = model.predict(sites[FEATURES])
sites["ghi_kwh_m2"] = sites["ALLSKY_SFC_SW_DWN"] * 365                  # POWER gives kWh/m²/day
sites["specific_yield"] = sites["yield_ratio"] * sites["ghi_kwh_m2"]     # kWh per kW installed per year
sites["annual_energy_mwh"] = sites["specific_yield"] * CAPACITY_MW

lo, hi = train[FEATURES].min(), train[FEATURES].max()                    # trees can't extrapolate beyond training data
sites["outside_training_range"] = sites[FEATURES].apply(
    lambda row: ", ".join(f for f in FEATURES if not lo[f] <= row[f] <= hi[f]), axis=1
)
sites.to_csv(c.RESULTS / "site_predictions.csv")
