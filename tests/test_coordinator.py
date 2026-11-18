"""Parser tests against saved idokep.hu pages.

These tests describe what the integration returns today, so later fixes show
up as clear, reviewable changes in the expected values.
"""

from __future__ import annotations

from datetime import datetime

import pytest
import pytz

from custom_components.idokep.coordinator import FetchWeatherData, generate_date

from .conftest import FIXTURE_TIME

BUDAPEST = pytz.timezone("Europe/Budapest")
VALID_CONDITIONS = {
    "clear-night",
    "cloudy",
    "exceptional",
    "fog",
    "hail",
    "lightning",
    "lightning-rainy",
    "partlycloudy",
    "pouring",
    "rainy",
    "snowy",
    "snowy-rainy",
    "sunny",
    "windy",
    "windy-variant",
}


@pytest.fixture
async def weather(fake_idokep, freezer):
    """Parse the saved Érd pages at the moment they were saved."""
    freezer.move_to(FIXTURE_TIME)
    return await FetchWeatherData("Érd", BUDAPEST, BUDAPEST, {"User-Agent": "test"})


async def test_requests_both_pages(weather, fake_idokep) -> None:
    """The current page and the hourly forecast page are downloaded."""
    assert fake_idokep.requested == [
        "https://www.idokep.hu/idojaras/Érd",
        "https://www.idokep.hu/elorejelzes/Érd",
    ]


async def test_current_weather(weather) -> None:
    """Current temperature and condition come from the current page."""
    current = weather["current"]
    assert current["native_temperature"] == "14"
    assert current["condition"] == "cloudy"
    assert current["native_temperature_unit"] == "°C"


async def test_daily_forecast(weather) -> None:
    """The daily columns become one forecast per day."""
    daily = weather["daily_forecast"]
    assert len(daily) == 15
    assert daily[0]["datetime"].startswith("2026-11-18")
    assert daily[1]["datetime"].startswith("2026-11-19")
    for day in daily:
        assert day["condition"] in VALID_CONDITIONS
        assert int(day["temperature"]) >= int(day["templow"])


async def test_hourly_forecast(weather) -> None:
    """Hourly cards have time zone aware times, wind and rain."""
    hourly = weather["hourly_forecast"]
    assert len(hourly) == 36
    times = [datetime.fromisoformat(hour["datetime"]) for hour in hourly]
    assert all(t.tzinfo is not None for t in times)
    assert times == sorted(times)
    assert times[0].hour == 14
    for hour in hourly:
        assert hour["condition"] in VALID_CONDITIONS
        assert hour["wind_speed"] is not None
        assert 0 <= hour["wind_bearing"] <= 360
    assert any(hour["precipitation"] > 0 for hour in hourly)


def test_generate_date_rolls_into_next_month(freezer) -> None:
    """A day number lower than today belongs to the next month."""
    freezer.move_to("2026-12-30T10:00:00")
    assert generate_date(31) == datetime(2026, 12, 31)
    assert generate_date(2) == datetime(2027, 1, 2)
