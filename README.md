# Időkép HomeAssistant Component

This is a Custom Component for Home-Assistant (https://home-assistant.io) reads and displays Időkép weather data and forecast.

## Installation

<ins>Manual:</ins>

- Copy directory idokep to your <config dir>/custom_components directory.

- Restart Home-Assistant

- Add new integration in Home Assistant under Settings -> Devices & services

- Enter the name of location in configuration window. (It shall be the same to the end string of URL in web browser when you get the forecast data)
    e.g.: **Pécs**  (https://www.idokep.hu/elorejelzes/Pécs)

## How it works

This custom component is made based on OpenWeatherMap component. (https://github.com/home-assistant/core/tree/dev/homeassistant/components/openweathermap)

The components provides actual weather, hourly & daily forecast data for selected location.

In every 20 minutes it fetches html data from idokep.hu, extracts forecasts information transforms to Home Assistant Weather platform.
