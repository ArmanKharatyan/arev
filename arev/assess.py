"""One-call site assessment: solar output and losses, farming alternative, land and construction cost, payback."""
import joblib
import pandas as pd

from arev import config as c
from arev.land_price import estimate as land_price
from arev.nasa import annual, climatology

BU_ACRE_TO_T_HA = 0.0673         # wheat: 60 lb/bu


def _outside(values, train, features):
    """Features where a site lies beyond the training data; tree models can't extrapolate there."""
    lo, hi = train[features].min(), train[features].max()
    return ", ".join(f for f in features if not lo[f] <= values[f] <= hi[f])


def assess_sites(sites, capacity_mw=1, tracking=0, use_land_cover=True):
    """sites: {name: (lat, lon)}. Needs the models trained by scripts 04 and 07."""
    loss_model, ag_model = joblib.load(c.LOSS_MODEL_FILE), joblib.load(c.AG_MODEL_FILE)
    loss_train = pd.read_csv(c.RESULTS / "loss_model_data.csv")
    ag_train = pd.read_csv(c.RESULTS / "ag_model_data.csv")
    if use_land_cover:
        from arev.land_cover import land_cover

    rows = []
    for name, (lat, lon) in sites.items():
        weather = pd.Series(annual(lat, lon, c.LOSS_NASA_PARAMS, c.YEAR)).replace(-999, float("nan"))
        weather["tracking"] = tracking
        climate = pd.Series(climatology(lat, lon, c.AG_FEATURES)).replace(-999, float("nan"))
        cover = land_cover(lat, lon) if use_land_cover else None
        land = land_price(lat, lon, cover)

        # solar: physics gives the ideal output, the loss model predicts what real plants deliver
        ghi = weather["ALLSKY_SFC_SW_DWN"] * 365                                   # kWh/m² per year
        ideal_kwh_kw = ghi * c.TILT_GAIN
        yield_ratio = loss_model.predict(weather[c.LOSS_FEATURES].to_frame().T)[0]
        actual_kwh_kw = yield_ratio * ghi
        energy_mwh = actual_kwh_kw * capacity_mw

        # money
        area_ha = c.HA_PER_MW * capacity_mw
        construction = capacity_mw * 1000 * c.CAPEX_USD_KW
        land_cost = land["price_usd_m2"] * area_ha * 10_000
        solar_revenue = energy_mwh * 1000 * c.TARIFF_USD_KWH
        solar_profit = solar_revenue - capacity_mw * 1000 * c.OM_USD_KW_YR
        wheat_t_ha = ag_model.predict(climate[c.AG_FEATURES].to_frame().T)[0] * BU_ACRE_TO_T_HA
        farm_revenue = wheat_t_ha * area_ha * c.WHEAT_PRICE_USD_T

        rows.append({
            "site": name, "lat": lat, "lon": lon, "capacity_mw": capacity_mw,
            "sunlight_kwh_m2_yr": ghi,
            "ideal_output_mwh_yr": ideal_kwh_kw * capacity_mw,
            "predicted_output_mwh_yr": energy_mwh,
            "lost_output_mwh_yr": (ideal_kwh_kw - actual_kwh_kw) * capacity_mw,
            "loss_pct": (1 - actual_kwh_kw / ideal_kwh_kw) * 100,
            "solar_revenue_usd_yr": solar_revenue,
            "solar_profit_usd_yr": solar_profit,
            "land_area_ha": area_ha,
            "land_cover_at_site": cover["center_class"] if use_land_cover else "assumed cropland",
            "wheat_yield_t_ha": wheat_t_ha,
            "farm_revenue_usd_yr": farm_revenue,
            "solar_vs_farm_revenue": solar_revenue / farm_revenue,
            "land_price_usd_m2": land["price_usd_m2"],
            "land_price_amd_m2": land["price_usd_m2"] * c.USD_AMD,
            "land_cost_usd": land_cost,
            "land_cost_range_usd": f"{land_cost / 2:,.0f} - {land_cost * 2:,.0f}",
            "construction_cost_usd": construction,
            "total_investment_usd": construction + land_cost,
            "payback_years": (construction + land_cost) / solar_profit if solar_profit > 0 else float("inf"),
            "solar_model_outside_range": _outside(weather, loss_train, c.LOSS_FEATURES),
            "farm_model_outside_range": _outside(climate, ag_train, c.AG_FEATURES),
        })
    return pd.DataFrame(rows).set_index("site")
