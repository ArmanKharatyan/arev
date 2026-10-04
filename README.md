# Arev

Know what a solar site will give, and what it will cost, before you build it.

Arev answers four questions for any coordinates, starting with Armenia:

| Question | How | Status |
|---|---|---|
| How much sun? | PVGIS and NASA POWER climate data | Working |
| What will we lose? | Model trained on ~1,000 real US solar plants: output per unit of sunlight from heat, dust, humidity, wind | Working |
| What happens to farming? | Model trained on US county wheat yields: agricultural potential of the land from climate | Working, prototype |
| Does it pay? | Build, land and running costs against electricity sales | Demo page |

Open `demo/arev.html` in a browser for the interactive site assessment of Yerevan.

## Setup

```bash
git clone <repo-url>
cd arev
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Download the raw files listed in [`data/README.md`](data/README.md) into `data/raw/`.

## Run

Run from the repository root, in order:

```bash
python scripts/01_build_dataset.py      # EIA plants: generation, coordinates, capacity
python scripts/02_fetch_weather.py      # NASA POWER weather per plant (first run ~15-30 min, then cached)
python scripts/03_fetch_land_cover.py   # optional: land cover around each plant
python scripts/04_train_loss_model.py   # train and evaluate the loss model
python scripts/05_predict_sites.py      # predict for the Armenian sites in arev/config.py
python scripts/06_site_climate.py       # PVGIS climate summary for the same sites
NASS_KEY=<your key> python scripts/07_train_ag_model.py   # agricultural potential (Windows: set NASS_KEY=... first)
```

Candidate sites, year, feature lists and file locations are all in `arev/config.py`.

## Outputs (`results/`)

| File | Content |
|---|---|
| `loss_model_scores.csv` | Cross-validated error of the linear and boosting models against a median baseline |
| `loss_model_importance.csv` | Which weather features drive the prediction (read only if the models beat the baseline) |
| `loss_model_correlation.csv`, `loss_model_by_state.csv`, `loss_model_summary.csv` | Exploratory analysis |
| `site_predictions.csv` | Predicted energy per kW and per year for each site, and features outside the training range |
| `site_climate_annual.csv`, `site_climate_monthly.csv` | PVGIS climate per site |
| `ag_model_scores.csv`, `ag_model_sites.csv` | Agricultural model accuracy and predicted wheat yield per site |

## How the loss model works

1. Clean-panel physics is not re-learned. The target is `yield_ratio`: a plant's annual output per kW divided by the sunlight it received. Low values mean losses.
2. Features are annual weather at the plant: clearness, albedo, aerosols (dust), cloud, temperature, temperature range, humidity, rain, wind, plus fixed vs. tracking panels.
3. Validation is grouped by NASA grid cell, so every score comes from locations the model never saw.
4. For a new site, `outside_training_range` lists features beyond what the US training plants covered. Tree models cannot extrapolate, so treat those predictions as rough.

## Limitations

- Training data is US-only and half of it is in California and North Carolina. No public Armenian plant data exists yet.
- Annual output also reflects outages and curtailment, not only weather.
- The agricultural model ignores irrigation and soil, so it underestimates irrigated land such as the Ararat valley.
- Prices and costs in the demo are editable assumptions, not quotes.

## Repository layout

```
arev/          shared code: config, EIA readers, NASA POWER, PVGIS, land cover
scripts/       pipeline steps, run in numbered order
data/          raw downloads and processed files (not committed)
results/       model outputs (not committed)
demo/          interactive site assessment page
```
