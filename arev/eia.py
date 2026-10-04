import pandas as pd


def load_generation(path, skiprows):
    """Annual net generation (MWh) of every solar PV plant in an EIA-923 workbook."""
    gen = pd.read_excel(path, sheet_name="Page 1 Generation and Fuel Data", skiprows=skiprows)
    gen.columns = gen.columns.str.replace("\n", " ").str.strip()          # EIA headers contain line breaks
    gen = gen[(gen["Reported Fuel Type Code"] == "SUN") & (gen["Reported Prime Mover"] == "PV")]
    gen = gen.rename(columns={gen.filter(regex="^Net Generation").columns[0]: "net_gen_mwh"})
    gen["net_gen_mwh"] = pd.to_numeric(gen["net_gen_mwh"], errors="coerce")   # EIA marks missing values with "."
    return gen[["Plant Id", "Plant Name", "Plant State", "net_gen_mwh"]]


def load_coordinates(path, skiprows):
    """Plant coordinates from the EIA-860 plant file, indexed by plant id."""
    plants = pd.read_excel(path, skiprows=skiprows)
    return plants.set_index("Plant Code")[["Latitude", "Longitude"]]


def load_capacity(path, skiprows):
    """Capacity (MW) and tracking flag per plant from EIA-860 3_3_Solar; a plant can have several generators."""
    solar = pd.read_excel(path, sheet_name="Operable", skiprows=skiprows)
    solar["tracking"] = (solar["Single-Axis Tracking?"].eq("Y") | solar["Dual-Axis Tracking?"].eq("Y")).astype(int)
    return solar.groupby("Plant Code").agg(capacity_mw=("Nameplate Capacity (MW)", "sum"), tracking=("tracking", "max"))
