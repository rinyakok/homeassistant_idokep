"""Weather data coordinator for the Idokep Weather service."""

from datetime import timedelta
import logging

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_SUNNY,
    WeatherEntityFeature,
    Forecast,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import sun
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from homeassistant.const import (
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)

from .const import (
    ATTR_API_CLOUDS,
    ATTR_API_CONDITION,
    ATTR_API_CURRENT,
    ATTR_API_DAILY_FORECAST,
    ATTR_API_DEW_POINT,
    ATTR_API_NATIVE_TEMPERATURE,
    ATTR_API_NATIVE_TEMPERATURE_UNIT,
    ATTR_API_HOURLY_FORECAST,
    ATTR_API_HUMIDITY,
    ATTR_API_PRECIPITATION_KIND,
    ATTR_API_PRESSURE,
    ATTR_API_RAIN,
    ATTR_API_SNOW,
    ATTR_API_TEMPERATURE,
    ATTR_API_UV_INDEX,
    ATTR_API_VISIBILITY_DISTANCE,
    ATTR_API_WEATHER,
    ATTR_API_WEATHER_CODE,
    ATTR_API_WIND_BEARING,
    ATTR_API_WIND_GUST,
    ATTR_API_WIND_SPEED,
    DOMAIN,
    DEFAULT_LOCATION,
    BASE_IDOKEP_URL,
)

_LOGGER = logging.getLogger(__name__)

WEATHER_UPDATE_INTERVAL = timedelta(minutes=20)

#=========================== SAJAT KÓD ========================================

import aiohttp
from datetime import datetime

weather_conditions = {
 'napos': 'sunny',
 'derült':  'sunny',
 'borult': 'cloudy',
 'erősen felhős': 'cloudy',
 'közepesen felhős': 'partlycloudy',
 'gyengén felhős': 'partlycloudy',
 'zivatar': 'lightning-rainy',
 'zápor': 'rainy',
 'szitálás': 'rainy',
 'gyenge eső': 'rainy',
 'eső': 'rainy',
 'eső viharos széllel': 'rainy',
 # The following conditions shall be tested/confirmed
 'köd': 'fog',
 'párás': 'fog',
 'pára': 'fog',
 'villámlás': 'lightning',
 'erős eső': 'pouring',
 'jégeső': 'hail',
 'havazás': 'snowy',
 'hószállingózás': 'snowy',
 'havas eső': 'snowy-rainy',
 'fagyott eső': 'snowy-rainy',
 'szeles': 'windy',
 'száraz zivatar': 'lightning',
#Not mapped 
#clear-night	Clear night
#exceptional	Exceptional
#windy-variant	Wind and clouds
}

wind_mapping = {
    'szélcsend': 0,   # 0-1 km/h
    'gyenge szellő': 4, #fuvallat (2-6 km/h)
    'enyhe': 9, # (7-11 km/h)
    'gyenge': 15, # (12-19 km/h)
    'mersekelt': 25, # (20-29 km/h)
    'elenk': 35, # (30-39 km/h)
    'eros': 45, # (40-49 km/h)
    'viharos': 55, # (50-60 km/h)
    'élénk viharos szél': 66, #(61-72 km/h)
    'heves vihar': 79, #(73-85 km/h)
    'dühöngő vihar': 93, # (86-100 km/h)
    'heves szélvész': 108, # (101-115 km/h)
    'orkán': 118, #(115-120 km/h)
}

from bs4 import BeautifulSoup, Comment
import re

#============== Generate forecast date from a day of month ================
def generate_date(forecast_day):
    # Get today's date
    today = datetime.today()
    day = today.day
    month = today.month
    year = today.year

    # Check if the input day is less than today's day
    if forecast_day < day:
        # Move to the next month
        if month == 12:  # December, next month is January of next year
            month = 1
            year += 1
        else:
            month += 1

    # Create the new date
    try:
        generated_date = datetime(year, month, forecast_day)
    except ValueError:
        _LOGGER.error(f"Invalid day_of_month: {forecast_day} for the month {month}")
        return f"Invalid day_of_month: {forecast_day} for the month {month}"

    return generated_date

#======================= Fetch Forecast data ============================
async def FetchWeatherData(location):

    if location == None:
        location = DEFAULT_LOCATION

    hourly_forecast_url = BASE_IDOKEP_URL + '/elorejelzes/' + location
    actual_weather_url = BASE_IDOKEP_URL+ '/idojaras/' + location

    _LOGGER.debug("Fetching data for location: " + location)
    _LOGGER.debug(hourly_forecast_url)

    # ====================== GETTING ACTUAL WEATHER ==================================

    async with aiohttp.ClientSession() as session:
        async with session.get(actual_weather_url) as response:
            html_string = await response.text()
            soup = BeautifulSoup(html_string, "html.parser")

            # Get Sunrise & Sunset times
            sunrise_txt = soup.find('img', attrs={'src': '/assets/icons/sunrise.svg'}).parent.text.lower().rstrip()[9:]
            sunset_txt = soup.find('img', attrs={'src': '/assets/icons/sunset.svg'}).parent.text.lower().rstrip()[10:]
            sunrise = datetime.strptime(datetime.now().strftime('%Y-%m-%d')+' ' + sunrise_txt, '%Y-%m-%d %H:%M')
            sunset = datetime.strptime(datetime.now().strftime('%Y-%m-%d')+' ' + sunset_txt, '%Y-%m-%d %H:%M')

            #Get Weather data
            actual_weather = soup.find('div', attrs={'class': 'ik current-weather'}).text.lower()
            actual_weather_icon = soup.find('div', attrs={'class': 'current-weather-lockup'}).find('img', attrs={'class': 'ik forecast-bigicon'}).get('src')
            actual_temperature = soup.find('div', attrs={'class': 'ik current-temperature'}).text.rstrip()
            #Get degree from string cut off the last two characters
            actual_temperature_value = actual_temperature[0:-2]
            #Get °C from the last two character od the string
            actual_temperature_unit = actual_temperature[-2:]
            #Getting mapped weather condition from tuple... if key doesn't exists return 'None'
            actual_weather_condition = weather_conditions.get(actual_weather, actual_weather)

            # IF current time is later than sunset time or earlier than sunrise time and weather condition is sunny => change condition to clear night
            if (datetime.now().time() > sunset.time()) or (datetime.now().time()< sunrise.time()):
                if actual_weather_condition == 'sunny':
                    actual_weather_condition = 'clear-night'

            _LOGGER.debug('Current Weather: ' + actual_temperature + '  ' + actual_weather + '   (' + actual_weather_icon +')    ' + actual_weather_condition)
        
        # ====================== GETTING DAILY FORECAST DATA ==================================
            daily_forecast_cols = soup.find('div', attrs={'id': 'dailyForecast'}).find_all('div', attrs={'class': 'dailyForecastCol'})

            daily_forecast_list = []

            for daily_data in daily_forecast_cols:
                day = int(daily_data.find('span', attrs={'class':re.compile("ik dfDayNum")}).text)
                daily_forecast_date = generate_date(day)
                weather_desc_pattern = r"<div[^>]*>\s*<img[^>]*>\s*([^<]+)"
                weather_desc_match = re.search(weather_desc_pattern, daily_data.find('div', attrs={'class': 'ik dfIconAlert'}).find('a').attrs['data-bs-content'])
                if weather_desc_match:
                    daily_weather = weather_desc_match.group(1).strip()
                daily_weather_condition = weather_conditions.get(daily_weather, daily_weather)
                daily_temperature_obj = daily_data.find('div', attrs={'class': 'ik min-max-container'}).find('a')
                daily_temperature_max = daily_temperature_obj.text
                daily_temperature_min = daily_temperature_obj.find_next('a').text
                daily_rain_level_obj = daily_data.find('div', attrs={'class': 'ik rainlevel-container'})
                if daily_rain_level_obj:
                        search_number_regex_pattern = r"'[\d]+"
                        rain_level = re.search(search_number_regex_pattern,(daily_rain_level_obj.find('a').find('span')['class'])[1]) or 0
                else:
                    rain_level = 0
                
                _LOGGER.debug('Date: '+ str(daily_forecast_date) + '  ' + str(daily_weather_condition) + ' max temp: ' + str(daily_temperature_max) + ' min temp: ' + str(daily_temperature_min) + ' rain level: ' + str(rain_level))

                # Add forecast element to forecast list
                daily_forecast_list.append (Forecast(
                    datetime=daily_forecast_date.isoformat(),
                    condition=daily_weather_condition,
                    temperature=daily_temperature_max,
                    templow=daily_temperature_min,
                    precipitation=rain_level,
                ))

        # ====================== GETTING HOURLY FORECAST DATA ==================================
        async with session.get(hourly_forecast_url) as response:
            html_string = await response.text()
            soup = BeautifulSoup(html_string, "html.parser")

            forecast_card_list = soup.find_all('div', attrs={'class': 'new-hourly-forecast-card'})

            start_hour = 0
            start_date = datetime.today()
            hourly_forecast_list = []

            for forecast_card in forecast_card_list:
                forecast_hour_str = forecast_card.find("div" , attrs={'class': 'ik new-hourly-forecast-hour'}, recursive=False).text
                forecast_hour = int(forecast_hour_str[0:-3])
                
                #It's a next day forcast if forecast hour is less than start_date => need to increase date by 1 day
                if forecast_hour < start_hour:
                    start_date += timedelta(days=1)
                
                start_hour = forecast_hour
                forecast_datetime = datetime.strptime(start_date.strftime('%Y-%m-%d') + ' ' + forecast_hour_str, '%Y-%m-%d %H:%M')

                forecast_weather_obj = forecast_card.find("div" , attrs={'class': 'ik forecast-icon-container'}, recursive=False).find("a", recursive=False)
                forecast_weather = forecast_weather_obj.get('data-bs-content')
                _LOGGER.debug('Forecast Weather Condition String: ' + str(forecast_weather))
                #Getting mapped weather condition from tuple... if key doesn't exists return None
                forecast_weather_condition = weather_conditions.get(forecast_weather, 'None')

                # IF forecast time is later than sunset time or earlier than sunrise time and weather condition is sunny => change condition to clear night
                if (forecast_datetime.time() > sunset.time()) or (forecast_datetime.time() < sunrise.time()):
                    if forecast_weather_condition == 'sunny':
                        forecast_weather_condition = 'clear-night'

                # get temperature value
                forecast_temperature_value = forecast_card.find("div", attrs={'class': 'ik tempBarGraph'}, recursive=False).find("div" , attrs={'class': 'ik tempValue'}, recursive=False).find("a", recursive=False).get_text().strip()

                #===== WIND ============

                forecast_wind_obj = str(forecast_card.find("div", attrs={'class': 'ik hourly-wind'}, recursive=False).find("a", recursive=False).find("div", recursive=False)['class']).split("', '")
                #Get wind force string 
                forecast_wind_force_str = forecast_wind_obj[-2]
                _LOGGER.debug('Wind force string: ' + forecast_wind_force_str)
                #Get wind direction string (degree) string is like 'r158'
                forecast_wind_direction = int(forecast_wind_obj[-1][1:-2])
                #Get mapped wind speed from wind force string
                forecast_wind_speed = wind_mapping.get(forecast_wind_force_str)
                _LOGGER.debug('Wind direction: ' + str(forecast_wind_direction))

                #===== RAIN =======
                precipitation_obj = forecast_card.find("div" , attrs={'class': 'ik hourly-rainlevel'}, recursive=True)
                if (precipitation_obj != None):
                    #Precipitation value in comment :)
                    precipitation_obj = precipitation_obj.find_all(string=lambda text: isinstance(text, Comment))
                    _precipitation = float(precipitation_obj[0][:-2]) or 0.0
                    _LOGGER.debug(_precipitation)
                    _precipitation_probability = forecast_card.find("div" , attrs={'class': 'ik hourly-rain-chance'}, recursive=False).find("a", recursive=False).get_text()[:-1]
                    _LOGGER.debug(_precipitation_probability)
                else:
                    _precipitation = 0.0
                    _precipitation_probability = 0
                #=================

                # Add forecast element to forecast list
                hourly_forecast_list.append (Forecast(
                    datetime=forecast_datetime.isoformat(),
                    condition=forecast_weather_condition,
                    temperature=forecast_temperature_value,
                    wind_speed=forecast_wind_speed,
                    wind_bearing=forecast_wind_direction,
                    precipitation_probability=_precipitation_probability,
                    precipitation=_precipitation,
                ))

        return {
            ATTR_API_CURRENT: {
            ATTR_API_CONDITION: actual_weather_condition, #self._get_condition(current_weather.condition.id),
            ATTR_API_NATIVE_TEMPERATURE: f"{actual_temperature_value}",
            ATTR_API_NATIVE_TEMPERATURE_UNIT: UnitOfTemperature.CELSIUS, #actual_temperature_unit,
            },
            ATTR_API_HOURLY_FORECAST: hourly_forecast_list,
            ATTR_API_DAILY_FORECAST: daily_forecast_list,
        }
#======================================================================================================

class WeatherUpdateCoordinator(DataUpdateCoordinator):
    """Weather data update coordinator."""

    def __init__(self, location: str, hass: HomeAssistant, ) -> None:
        """Initialize coordinator."""
        self._location = location
        self._attr_supported_features = (
            WeatherEntityFeature.FORECAST_DAILY |
            WeatherEntityFeature.FORECAST_HOURLY
            )

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=WEATHER_UPDATE_INTERVAL
        )

    async def _async_update_data(self):
        """Update the data."""
        weather_data = await FetchWeatherData(self._location)
        return weather_data
