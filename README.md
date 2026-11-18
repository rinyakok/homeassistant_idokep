# Időkép Weather for Home Assistant

Weather data and forecasts from [idokep.hu](https://www.idokep.hu) for places in Hungary.

**[Magyar leírás (részletes) →](https://github.com/rinyakok/homeassistant_idokep/blob/main/README.hu.md)**

## Features

- Weather entity with current conditions, a 15-day daily forecast and a 36-hour hourly forecast (temperature, wind, precipitation)
- Sensors: temperature, condition (also in Hungarian), short text forecast, sunrise, sunset
- Binary sensors: thunderstorm in the next hour, connection to idokep.hu
- Any number of locations, one device per location
- English and Hungarian user interface

## Installation

**HACS (recommended):** open HACS, search for **Időkép**, download **Időkép Weather Component**, then restart Home Assistant.

![HACS](https://github.com/user-attachments/assets/3d409403-e481-4b48-a9b8-7c2794d578a1)

**Manual:** copy `custom_components/idokep` into your `<config>/custom_components` folder and restart Home Assistant.

## Setup

1. Go to **Settings → Devices & services → Add integration** and choose **Időkép**.
2. Type the name of the place as written on idokep.hu, for example **Pécs** (`https://www.idokep.hu/idojaras/Pécs`). Accents are optional.
3. Repeat for more places.

To change a place later, use **Reconfigure** on the integration entry. Entity IDs stay the same.

## Entities (for a place called Érd)

| Entity | Description |
|---|---|
| `weather.idokep_erd` | Current weather, daily and hourly forecast |
| `sensor.idokep_erd_temperature` | Current temperature (°C) |
| `sensor.idokep_erd_condition` | Current condition (Home Assistant condition, e.g. `rainy`) |
| `sensor.idokep_erd_condition_hungarian` | Current condition as written on idokep.hu (e.g. "Erősen felhős") |
| `sensor.idokep_erd_short_forecast` | Short text forecast (e.g. "Kettősfronti hatás várható") |
| `sensor.idokep_erd_sunrise`, `sensor.idokep_erd_sunset` | Today's sunrise and sunset |
| `binary_sensor.idokep_erd_storm_in_the_next_hour` | On if a thunderstorm is forecast for the current or next hour |
| `binary_sensor.idokep_erd_connection` | Off when idokep.hu can't be reached (diagnostic) |

The weather entity also has the attributes `short_forecast`, `precipitation` and `precipitation_probability` (forecast for the next hour).

Entity IDs follow your Home Assistant language when the entity is created; the examples are for English.

## Switching from FabianGabor/HA-Idokep

Both integrations use the `idokep` domain, so only one can be installed. Remove HA-Idokep in HACS (keep its integration entries), install this one, and restart. The entries are taken over automatically and the entity IDs stay the same. Details in the [Hungarian guide](https://github.com/rinyakok/homeassistant_idokep/blob/main/README.hu.md#átállás-a-ha-idokep-integrációról).

## How it works

Every 20 minutes the integration downloads two pages from idokep.hu for each place and reads the weather data from them. It does not use an official API, so a change on the website can break parts of it. Please report problems in the [issue tracker](https://github.com/rinyakok/homeassistant_idokep/issues).
