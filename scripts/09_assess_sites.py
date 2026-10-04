"""Full assessment for any coordinates. Edit SITES and run; needs scripts 04 and 07 to have been run once."""
from arev import config as c
from arev.assess import assess_sites

SITES = {                        # name: (lat, lon)
    "Mets Masrik": (40.21, 45.76),
    "Sisian": (39.52, 46.03),
}
CAPACITY_MW = 1
TRACKING = 0                     # 0 = fixed panels, 1 = tracker
USE_LAND_COVER = True            # False skips Planetary Computer and treats every site as cropland

results = assess_sites(SITES, CAPACITY_MW, TRACKING, USE_LAND_COVER)
results.to_csv(c.RESULTS / "site_assessment.csv")
print(results.T.to_string(float_format=lambda v: f"{v:,.2f}"))
