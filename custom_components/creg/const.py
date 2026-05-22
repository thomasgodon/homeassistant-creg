from datetime import timedelta

DOMAIN = "creg"
CSV_URL = "https://www.creg.be/sites/default/files/assets/Prices/CREG_Tariff_EV.csv"
REGIONS = ["flanders", "brussels", "wallonia"]
SCAN_INTERVAL = timedelta(hours=6)
UNIT = "c€/kWh"
