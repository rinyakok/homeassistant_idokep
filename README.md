# Időkép Weather for Home Assistant

Weather data and forecasts from [idokep.hu](https://www.idokep.hu) for places in Hungary.

**[Magyar leírás (részletes) →](https://github.com/rinyakok/homeassistant_idokep/blob/main/README.hu.md)**

## Features

- Weather entity with current conditions, a 15-day daily forecast and a 36-hour hourly forecast (temperature, wind, precipitation)
- Temperature and condition sensors
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

## Switching from FabianGabor/HA-Idokep

Both integrations use the `idokep` domain, so only one can be installed. Remove HA-Idokep in HACS (keep its integration entries), install this one, and restart. The entries are taken over automatically and the entity IDs stay the same. Details in the [Hungarian guide](https://github.com/rinyakok/homeassistant_idokep/blob/main/README.hu.md#átállás-a-ha-idokep-integrációról).

## How it works

Every 20 minutes the integration downloads two pages from idokep.hu for each place and reads the weather data from them. It does not use an official API, so a change on the website can break parts of it. Please report problems in the [issue tracker](https://github.com/rinyakok/homeassistant_idokep/issues).
