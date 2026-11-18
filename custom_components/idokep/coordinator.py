"""Weather data coordinator for the Idokep Weather service."""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, time, timedelta, tzinfo

import aiohttp
from bs4 import BeautifulSoup, Comment, Tag
from homeassistant.components.weather import (
    Forecast,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTemperature,
)
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.loader import async_get_integration
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_API_CONDITION,
    ATTR_API_CURRENT,
    ATTR_API_DAILY_FORECAST,
    ATTR_API_HOURLY_FORECAST,
    ATTR_API_LOCATION,
    ATTR_API_NATIVE_TEMPERATURE,
    ATTR_API_NATIVE_TEMPERATURE_UNIT,
    BASE_IDOKEP_URL,
    CONF_LOCATION,
    DEFAULT_LOCATION,
    DOMAIN,
    USER_AGENT_TEMPLATE,
    entry_unique_id,
)

_LOGGER = logging.getLogger(__name__)

WEATHER_UPDATE_INTERVAL = timedelta(minutes=20)
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)
BUDAPEST_TZ_NAME = "Europe/Budapest"

# Exceptions that mean "this part of the page is missing or has changed".
PARSE_ERRORS = (AttributeError, IndexError, KeyError, TypeError, ValueError)

weather_conditions = {
    "napos": "sunny",
    "derült": "sunny",
    "borult": "cloudy",
    "erősen felhős": "cloudy",
    "közepesen felhős": "partlycloudy",
    "gyengén felhős": "partlycloudy",
    "zivatar": "lightning-rainy",
    "zápor": "rainy",
    "szitálás": "rainy",
    "gyenge eső": "rainy",
    "eső": "rainy",
    "eső viharos széllel": "rainy",
    # The following conditions shall be tested/confirmed
    "köd": "fog",
    "ködös": "fog",
    "ködszitálás": "fog",
    "párás": "fog",
    "pára": "fog",
    "villámlás": "lightning",
    "erős eső": "pouring",
    "jégeső": "hail",
    "havazás": "snowy",
    "intenzív havazás": "snowy",
    "hószállingózás": "snowy",
    "hófúvás": "snowy",
    "hófúvás havazással": "snowy",
    "hózápor": "snowy",
    "havas eső": "snowy-rainy",
    "fagyott eső": "snowy-rainy",
    "ónos eső": "snowy-rainy",
    "szeles": "windy",
    "száraz zivatar": "lightning",
    "porvihar": "exceptional",
}

wind_mapping = {
    "szélcsend": 0,  # 0-1 km/h
    "gyenge szellő": 4,  # fuvallat (2-6 km/h)
    "enyhe": 9,  # (7-11 km/h)
    "gyenge": 15,  # (12-19 km/h)
    "mersekelt": 25,  # (20-29 km/h)
    "elenk": 35,  # (30-39 km/h)
    "eros": 45,  # (40-49 km/h)
    "viharos": 55,  # (50-60 km/h)
    "élénk viharos szél": 66,  # (61-72 km/h)
    "heves vihar": 79,  # (73-85 km/h)
    "dühöngő vihar": 93,  # (86-100 km/h)
    "heves szélvész": 108,  # (101-115 km/h)
    "orkán": 118,  # (115-120 km/h)
}

HUNGARIAN_MONTHS = {
    "január": 1,
    "február": 2,
    "március": 3,
    "április": 4,
    "május": 5,
    "június": 6,
    "július": 7,
    "augusztus": 8,
    "szeptember": 9,
    "október": 10,
    "november": 11,
    "december": 12,
}

# Unknown condition texts already logged, so each one is logged only once.
_unknown_conditions: set[str] = set()


def map_condition(text: str | None) -> str | None:
    """Map an idokep.hu condition text to a Home Assistant condition.

    Unknown texts return None (state "unknown") instead of an invalid
    condition, and are logged once so they can be added to the mapping.
    """
    if not text:
        return None
    key = " ".join(text.split()).lower()
    condition = weather_conditions.get(key)
    if condition is None and key not in _unknown_conditions:
        _unknown_conditions.add(key)
        _LOGGER.warning(
            "Unknown idokep.hu weather condition %r, please report it so it can "
            "be mapped",
            key,
        )
    return condition


class MissingElementError(ValueError):
    """An expected element is not on the idokep.hu page."""


def _find_optional(
    parent: Tag, name: str, recursive: bool = True, **attrs
) -> Tag | None:
    """Find a child element; None if it is not on the page."""
    if "class_" in attrs:
        attrs["class"] = attrs.pop("class_")
    found = parent.find(name, attrs=attrs, recursive=recursive)
    return found if isinstance(found, Tag) else None


def _find(parent: Tag, name: str, recursive: bool = True, **attrs) -> Tag:
    """Find a child element, or raise MissingElementError if it is missing."""
    found = _find_optional(parent, name, recursive, **attrs)
    if found is None:
        raise MissingElementError(f"<{name} {attrs}> not found")
    return found


def _text(element: Tag | None) -> str | None:
    """Return the text of an optional element."""
    return element.get_text() if element is not None else None


def _first_int(text: str | None) -> int | None:
    """Return the first (possibly negative) whole number in a text."""
    match = re.search(r"-?\d+", text or "")
    return int(match.group()) if match else None


def _first_float(text: str | None) -> float | None:
    """Return the first number in a text, accepting a decimal comma."""
    match = re.search(r"\d+(?:[.,]\d+)?", text or "")
    return float(match.group().replace(",", ".")) if match else None


# ============== Generate forecast date from a day of month ================
def generate_date(forecast_day: int, today: date | None = None) -> date | None:
    """Return the date for a day of month, on or after today.

    A day lower than today's day belongs to the next month. Returns None if
    the day does not exist in that month.
    """
    if today is None:
        today = dt_util.now(dt_util.get_default_time_zone()).date()
    year, month = today.year, today.month
    if forecast_day < today.day:
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    try:
        return date(year, month, forecast_day)
    except ValueError:
        _LOGGER.warning(
            "Invalid day of month %s for month %s, day skipped", forecast_day, month
        )
        return None


def _parse_title_date(title: str | None) -> date | None:
    """Parse a daily column title like 'Szerda<br>2026. november 18.'."""
    match = re.search(r"(\d{4})\.\s*([^\W\d_]+)\s+(\d{1,2})\.", title or "")
    if not match:
        return None
    month = HUNGARIAN_MONTHS.get(match.group(2).lower())
    if month is None:
        return None
    try:
        return date(int(match.group(1)), month, int(match.group(3)))
    except ValueError:
        return None


def parse_location_name(soup: BeautifulSoup) -> str | None:
    """Return the place idokep.hu really shows, from the page title.

    idokep.hu shows Budapest for unknown place names, without an error, so
    the title ("Érd időjárás - Időkép") is the only way to notice it.
    """
    title = soup.find("title")
    if title is None:
        return None
    match = re.match(r"\s*(.+?)\s+időjárás\b", title.get_text())
    return match.group(1) if match else None


def _parse_sun_times(
    soup: BeautifulSoup, today: date, budapest_tz: tzinfo
) -> tuple[datetime | None, datetime | None]:
    """Return today's sunrise and sunset, or None when not on the page."""
    result: list[datetime | None] = []
    for icon, alt in (("sunrise", "Napkelte"), ("sunset", "Napnyugta")):
        img = soup.find("img", src=re.compile(rf"{icon}\.svg")) or soup.find(
            "img", alt=alt
        )
        match = re.search(r"(\d{1,2}):(\d{2})", img.parent.get_text()) if img else None
        if match is None:
            _LOGGER.debug("No %s time found on the page", icon)
            result.append(None)
            continue
        result.append(
            datetime.combine(
                today,
                time(int(match.group(1)), int(match.group(2))),
                tzinfo=budapest_tz,
            )
        )
    return result[0], result[1]


def _is_night(
    moment: datetime, sunrise: datetime | None, sunset: datetime | None
) -> bool:
    """Return True if the time of day is before sunrise or after sunset."""
    if sunrise is None or sunset is None:
        return False
    return moment.time() > sunset.time() or moment.time() < sunrise.time()


def _night_condition(
    condition: str | None,
    moment: datetime,
    sunrise: datetime | None,
    sunset: datetime | None,
) -> str | None:
    """Use clear-night instead of sunny at night."""
    if condition == "sunny" and _is_night(moment, sunrise, sunset):
        return "clear-night"
    return condition


def _parse_current(
    soup: BeautifulSoup,
    now: datetime,
    sunrise: datetime | None,
    sunset: datetime | None,
) -> dict:
    """Parse the current condition and temperature."""
    condition = None
    temperature = None

    weather_div = soup.find("div", attrs={"class": "current-weather"})
    if weather_div is not None:
        condition = _night_condition(
            map_condition(weather_div.get_text()), now, sunrise, sunset
        )
    else:
        _LOGGER.warning("Current weather condition not found on idokep.hu page")

    temperature_div = soup.find("div", attrs={"class": "ik current-temperature"})
    if temperature_div is not None:
        temperature = _first_int(temperature_div.get_text())
    else:
        _LOGGER.warning("Current temperature not found on idokep.hu page")

    return {
        ATTR_API_CONDITION: condition,
        ATTR_API_NATIVE_TEMPERATURE: temperature,
        ATTR_API_NATIVE_TEMPERATURE_UNIT: UnitOfTemperature.CELSIUS,
    }


def _parse_daily_column(
    column: Tag, today: date, budapest_tz: tzinfo, local_tz: tzinfo
) -> Forecast | None:
    """Parse one daily forecast column."""
    icon_link = _find(_find(column, "div", class_="ik dfIconAlert"), "a")

    # The full date is in the title ("Szerda<br>2026. november 18."). The day
    # number is only a fallback, because it can't tell the month on its own.
    forecast_date = _parse_title_date(icon_link.get("title"))
    if forecast_date is None:
        day_span = _find(column, "span", class_=re.compile("dfDayNum"))
        forecast_date = generate_date(int(day_span.get_text()), today)
    if forecast_date is None:
        return None

    description = re.search(
        r"<div[^>]*>\s*<img[^>]*>\s*([^<]+)", icon_link.get("data-bs-content", "")
    )
    condition = map_condition(description.group(1) if description else None)

    links = _find(column, "div", class_="ik min-max-container").find_all("a")
    temperature_max = _first_int(links[0].get_text())
    temperature_min = _first_int(links[1].get_text()) if len(links) > 1 else None

    # "17 mm" when an amount is forecast; "." means only a trace.
    precipitation = 0.0
    rain = column.find("div", attrs={"class": "ik rainlevel-container"})
    if rain is not None:
        amount = rain.find("span", attrs={"class": "ik mm"})
        if amount is not None:
            precipitation = _first_float(amount.get_text()) or 0.0

    forecast_datetime = datetime.combine(
        forecast_date, time(0, 0), tzinfo=budapest_tz
    ).astimezone(local_tz)

    return Forecast(
        datetime=forecast_datetime.isoformat(),
        condition=condition,
        temperature=temperature_max,
        templow=temperature_min,
        precipitation=precipitation,
    )


def _parse_daily(
    soup: BeautifulSoup, today: date, budapest_tz: tzinfo, local_tz: tzinfo
) -> list[Forecast]:
    """Parse the daily forecast; a broken column is skipped, not fatal."""
    container = soup.find("div", attrs={"id": "dailyForecastContainer"})
    if container is None:
        _LOGGER.warning("Daily forecast not found on idokep.hu page")
        return []

    forecasts = []
    for column in container.find_all("div", attrs={"class": "dailyForecastCol"}):
        try:
            forecast = _parse_daily_column(column, today, budapest_tz, local_tz)
        except PARSE_ERRORS as err:
            _LOGGER.debug("Skipping daily forecast column: %r", err)
            continue
        if forecast is not None:
            forecasts.append(forecast)
    return forecasts


def _parse_hourly_card(
    card: Tag,
    hour: int,
    forecast_day: date,
    budapest_tz: tzinfo,
    local_tz: tzinfo,
    sunrise: datetime | None,
    sunset: datetime | None,
) -> Forecast:
    """Parse one hourly forecast card for the given day."""
    forecast_datetime = datetime.combine(
        forecast_day, time(hour, 0), tzinfo=budapest_tz
    )

    icon_container = _find(card, "div", False, class_="ik forecast-icon-container")
    icon_link = _find(icon_container, "a", False)
    condition = _night_condition(
        map_condition(icon_link.get("data-bs-content")),
        forecast_datetime,
        sunrise,
        sunset,
    )

    temperature_bar = _find(card, "div", False, class_="ik tempBarGraph")
    temperature_value = _find(temperature_bar, "div", False, class_="ik tempValue")
    temperature = _first_int(_find(temperature_value, "a", False).get_text())

    # Wind force is the last CSS class (e.g. 'gyenge'), the direction is in
    # the style attribute: style="--rotateAngle:158deg"
    wind_speed = None
    wind_bearing = None
    wind_link = _find(_find(card, "div", False, class_="ik hourly-wind"), "a", False)
    wind_div = _find_optional(wind_link, "div", False)
    if wind_div is not None:
        wind_classes = wind_div.get_attribute_list("class")
        wind_speed = wind_mapping.get(wind_classes[-1]) if wind_classes else None
        style = str(wind_div.attrs.get("style", ""))
        rotate = re.search(r"--rotateAngle:\s*(\d+)deg", style)
        wind_bearing = int(rotate.group(1)) if rotate else None

    # The precipitation amount is in an HTML comment ("<!--7 mm-->").
    precipitation = 0.0
    precipitation_probability = 0
    rain_level = card.find("div", attrs={"class": "ik hourly-rainlevel"})
    if rain_level is not None:
        comment = rain_level.find(string=lambda text: isinstance(text, Comment))
        precipitation = _first_float(comment) or 0.0
        chance = _find_optional(card, "div", False, class_="ik hourly-rain-chance")
        precipitation_probability = _first_int(_text(chance))

    return Forecast(
        datetime=forecast_datetime.astimezone(local_tz).isoformat(),
        condition=condition,
        temperature=temperature,
        wind_speed=wind_speed,
        wind_bearing=wind_bearing,
        precipitation_probability=precipitation_probability,
        precipitation=precipitation,
    )


def _parse_hourly(
    soup: BeautifulSoup,
    now: datetime,
    budapest_tz: tzinfo,
    local_tz: tzinfo,
    sunrise: datetime | None,
    sunset: datetime | None,
) -> list[Forecast]:
    """Parse the hourly forecast; a broken card is skipped, not fatal."""
    forecasts = []
    forecast_day = now.date()
    previous_hour = now.hour

    for card in soup.find_all("div", attrs={"class": "wide-hourly-forecast-card"}):
        try:
            hour_div = _find(card, "div", False, class_="ik wide-hourly-forecast-hour")
            hour = int(hour_div.get_text().strip()[0:-3])
        except PARSE_ERRORS as err:
            _LOGGER.debug("Skipping hourly forecast card: %r", err)
            continue

        # A lower hour than the previous card means the next day started.
        if hour < previous_hour:
            forecast_day += timedelta(days=1)
        previous_hour = hour

        try:
            forecasts.append(
                _parse_hourly_card(
                    card, hour, forecast_day, budapest_tz, local_tz, sunrise, sunset
                )
            )
        except PARSE_ERRORS as err:
            _LOGGER.debug("Skipping hourly forecast card: %r", err)
    return forecasts


async def _fetch_page(
    session: aiohttp.ClientSession, url: str, request_headers: dict | None
) -> BeautifulSoup:
    """Download one idokep.hu page."""
    async with session.get(
        url, headers=request_headers, timeout=REQUEST_TIMEOUT
    ) as response:
        response.raise_for_status()
        return BeautifulSoup(await response.text(), "html.parser")


# ======================= Fetch Forecast data ============================
async def FetchWeatherData(
    session: aiohttp.ClientSession,
    location: str | None,
    local_tz: tzinfo,
    budapest_tz: tzinfo,
    request_headers: dict | None = None,
) -> dict:
    """Download and parse the current weather and the forecasts."""
    if location is None:
        location = DEFAULT_LOCATION

    _LOGGER.debug("Fetching data for location: %s", location)
    now = datetime.now(budapest_tz)

    current_page = await _fetch_page(
        session, f"{BASE_IDOKEP_URL}/idojaras/{location}", request_headers
    )
    resolved_location = parse_location_name(current_page)
    sunrise, sunset = _parse_sun_times(current_page, now.date(), budapest_tz)
    current = _parse_current(current_page, now, sunrise, sunset)
    daily = _parse_daily(current_page, now.date(), budapest_tz, local_tz)

    hourly_page = await _fetch_page(
        session, f"{BASE_IDOKEP_URL}/elorejelzes/{location}", request_headers
    )
    hourly = _parse_hourly(hourly_page, now, budapest_tz, local_tz, sunrise, sunset)

    if current[ATTR_API_NATIVE_TEMPERATURE] is None and not daily and not hourly:
        raise UpdateFailed(
            f"No weather data found on idokep.hu for {location!r}; "
            "the location may be wrong or the website has changed"
        )

    return {
        ATTR_API_LOCATION: resolved_location,
        ATTR_API_CURRENT: current,
        ATTR_API_HOURLY_FORECAST: hourly,
        ATTR_API_DAILY_FORECAST: daily,
    }


# ==========================================================================


async def async_request_headers(hass: HomeAssistant) -> dict[str, str]:
    """Return the HTTP headers: an honest User-Agent with versions."""
    integration = await async_get_integration(hass, DOMAIN)
    return {
        "User-Agent": USER_AGENT_TEMPLATE.format(
            integration_version=integration.version,
            ha_version=HA_VERSION,
        )
    }


class WeatherUpdateCoordinator(DataUpdateCoordinator):
    """Weather data update coordinator."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self._location: str = entry.data[CONF_LOCATION]
        self._fallback_logged = False
        self._attr_supported_features = (
            WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
        )
        self.local_tz: tzinfo | None = None
        self.budapest_tz: tzinfo | None = None
        self.request_headers: dict | None = None
        self.local_tz_name = hass.config.time_zone or BUDAPEST_TZ_NAME
        _LOGGER.debug("Local time zone name: %s", self.local_tz_name)

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {self._location}",
            update_interval=WEATHER_UPDATE_INTERVAL,
        )

    async def _async_update_data(self):
        """Update the data."""
        if self.local_tz is None:
            self.local_tz = await dt_util.async_get_time_zone(self.local_tz_name)
        if self.budapest_tz is None:
            self.budapest_tz = await dt_util.async_get_time_zone(BUDAPEST_TZ_NAME)

        if self.request_headers is None:
            self.request_headers = await async_request_headers(self.hass)
            _LOGGER.debug("Request User-Agent: %s", self.request_headers["User-Agent"])

        try:
            data = await FetchWeatherData(
                async_get_clientsession(self.hass),
                self._location,
                self.local_tz,
                self.budapest_tz,
                self.request_headers,
            )
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error fetching data from idokep.hu: {err}") from err

        resolved = data[ATTR_API_LOCATION]
        if (
            resolved
            and entry_unique_id(resolved) != entry_unique_id(self._location)
            and not self._fallback_logged
        ):
            self._fallback_logged = True
            _LOGGER.warning(
                "idokep.hu does not know the location %r and shows %r instead; "
                "please correct the location (Reconfigure)",
                self._location,
                resolved,
            )
        return data
