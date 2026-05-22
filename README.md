# CREG Tariff — Home Assistant Integration

<img src="custom_components/creg/brand/icon.png" alt="CREG Tariff logo" width="64" align="right"/>

Home Assistant custom integration that exposes the official [CREG](https://www.creg.be) home-charging reimbursement tariffs for company electric vehicles in Belgium.

Data source: [CREG — Tarief voor terugbetaling thuisladen bedrijfswagens](https://www.creg.be/nl/consumenten/prijzen-en-tarieven/creg-tarief-voor-terugbetaling-thuisladen-bedrijfswagens)

Tariffs are fetched every 6 hours from the official CREG CSV file.

---

## Sensors

Six sensors are created, grouped under a single **CREG Tariff** device:

| Entity ID | Description |
|---|---|
| `sensor.creg_tariff_flanders` | Latest monthly End-user Price EV for Flanders (c€/kWh) |
| `sensor.creg_tariff_brussels` | Latest monthly End-user Price EV for Brussels (c€/kWh) |
| `sensor.creg_tariff_wallonia` | Latest monthly End-user Price EV for Wallonia (c€/kWh) |
| `sensor.creg_tariff_flanders_avg_3m` | Latest official CREG 3-month average tariff for Flanders (c€/kWh) |
| `sensor.creg_tariff_brussels_avg_3m` | Latest official CREG 3-month average tariff for Brussels (c€/kWh) |
| `sensor.creg_tariff_wallonia_avg_3m` | Latest official CREG 3-month average tariff for Wallonia (c€/kWh) |

### Price sensors (`sensor.creg_tariff_*`)

State: latest available monthly End-user Price EV in `c€/kWh`.

Attributes:
- `data` — full parsed dataset (all months, all regions) as a list of objects
- `latest_year` / `latest_month` — year and month of the latest data point

### Avg 3M sensors (`sensor.creg_tariff_*_avg_3m`)

State: the most recently published official CREG 3-month average tariff in `c€/kWh`. This is the value used by employers to calculate EV home-charging reimbursements. Updated quarterly (Jan/Apr/Jul/Oct).

Attributes:
- `period_year` / `period_month` — the quarter-start month the average applies to

---

## Installation

### Via HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/thomasgodon/homeassistant-creg` with category **Integration**
3. Search for "CREG Tariff" and install
4. Restart Home Assistant
5. Go to **Settings → Devices & Services → Add Integration** → search "CREG Tariff"

### Manual

1. Copy `custom_components/creg/` into your HA `config/custom_components/` folder
2. Restart Home Assistant
3. Add the integration via **Settings → Devices & Services → Add Integration → CREG Tariff**

---

## Example: monthly reimbursement calculation

Use the official CREG avg 3M sensor to calculate what your employer owes you for home-charging. Replace `your_monthly_kwh` with a helper or energy sensor reading:

```yaml
template:
  - sensor:
      - name: "EV reimbursement this month"
        unit_of_measurement: "€"
        state: >
          {% set rate = states('sensor.creg_tariff_flanders_avg_3m') | float(0) %}
          {% set kwh = states('sensor.ev_home_charging_energy_monthly') | float(0) %}
          {{ ((rate / 100) * kwh) | round(2) }}
```

---

## Notes

- Flanders uses the **digital meter** rate; Brussels and Wallonia use the **classic meter** rate — matching the CSV columns.
- The 3-month average is computed by CREG using a 2-month delay (`M-2` to `M-4`), ensuring all regional network tariff data is available.
- All values are all-in (energy cost + network cost + levies + surcharges + VAT).

## Branding

Brand assets live in `custom_components/creg/brand/`:
- `icon.svg` — source design (Pillow-rendered via `render_icons.py`)
- `icon.png` / `icon@2x.png` — 256×256 and 512×512 raster exports

To regenerate the PNGs after editing the Python render script: `python custom_components/creg/brand/render_icons.py`

## Attribution

Data © [CREG — Commission de Régulation de l'Électricité et du Gaz](https://www.creg.be)
