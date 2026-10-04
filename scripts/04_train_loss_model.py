"""Train and evaluate the loss model: how much output per unit of sunlight each plant delivers."""
import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold, cross_val_predict

from arev import config as c

FEATURES = c.LOSS_FEATURES

# %% target: output per unit of sunlight
data = pd.read_csv(c.PLANTS_WEATHER_FILE)
data["specific_yield"] = data["net_gen_mwh"] / data["capacity_mw"]       # kWh per kW = full-power hours per year
data["capacity_factor"] = data["specific_yield"] / 8760
data["ghi_kwh_m2"] = data["ALLSKY_SFC_SW_DWN"] * 365                      # POWER gives kWh/m²/day
data["yield_ratio"] = data["specific_yield"] / data["ghi_kwh_m2"]         # performance-ratio-like, ~0.8-1.2

data = data[data["capacity_factor"].between(0.08, 0.40)]                  # drop partial-year, offline, or bad-capacity plants
data = data.dropna(subset=FEATURES + ["yield_ratio"]).reset_index(drop=True)

# %% exploratory analysis
summary = data[["capacity_factor", "yield_ratio", *FEATURES]].describe().T
correlation = data[FEATURES + ["yield_ratio"]].corr()["yield_ratio"].drop("yield_ratio").sort_values()
by_state = data.groupby("Plant State")["yield_ratio"].agg(["count", "median"]).sort_values("count", ascending=False)

# %% models, validated on unseen grid cells (plants in one cell share weather)
X, y = data[FEATURES], data["yield_ratio"]
groups = data["lat_cell"].astype(str) + "_" + data["lon_cell"].astype(str)
models = {
    "linear": LinearRegression(),
    "boosting": HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=300, random_state=0),
}
predictions = {name: cross_val_predict(m, X, y, groups=groups, cv=GroupKFold(n_splits=5)) for name, m in models.items()}
scores = pd.DataFrame({name: {"MAE": mean_absolute_error(y, p), "R2": r2_score(y, p)} for name, p in predictions.items()}).T
scores.loc["baseline_median"] = [mean_absolute_error(y, [y.median()] * len(y)), 0.0]

# %% final model and feature importance (only meaningful if the models beat baseline_median)
final = models["boosting"].fit(X, y)
imp = permutation_importance(final, X, y, n_repeats=20, random_state=0)
importance = pd.Series(imp.importances_mean, index=FEATURES).sort_values(ascending=False)

data["predicted_ratio"] = predictions["boosting"]
joblib.dump(final, c.LOSS_MODEL_FILE)
for name, table in {"summary": summary, "correlation": correlation, "by_state": by_state,
                    "scores": scores, "importance": importance, "data": data}.items():
    table.to_csv(c.RESULTS / f"loss_model_{name}.csv")
