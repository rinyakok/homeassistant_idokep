"""Parser tests against saved idokep.hu pages."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from bs4 import BeautifulSoup
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.idokep import coordinator
from custom_components.idokep.binary_sensor import storm_expected
from custom_components.idokep.coordinator import (
    FetchWeatherData,
    generate_date,
    map_condition,
)

from .conftest import FIXTURE_TIME, FakeClientSession, load_fixture, pages_with_alerts

BUDAPEST = ZoneInfo("Europe/Budapest")
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


def _without(page: str, *selectors: str) -> str:
    """Return the page with the given CSS selectors removed."""
    soup = BeautifulSoup(page, "html.parser")
    for selector in selectors:
        for tag in soup.select(selector):
            tag.decompose()
    return str(soup)


async def _fetch(session: FakeClientSession, local_tz=BUDAPEST) -> dict:
    return await FetchWeatherData(
        session, "Érd", local_tz, BUDAPEST, {"User-Agent": "test"}
    )


@pytest.fixture
async def weather(freezer):
    """Parse the saved Érd pages at the moment they were saved."""
    freezer.move_to(FIXTURE_TIME)
    session = FakeClientSession()
    data = await _fetch(session)
    data["session"] = session
    return data


async def test_requests_both_pages_with_headers(weather) -> None:
    """Both pages are downloaded with the integration's User-Agent."""
    session = weather["session"]
    assert session.requested == [
        "https://www.idokep.hu/idojaras/Érd",
        "https://www.idokep.hu/elorejelzes/Érd",
    ]
    assert session.headers == [{"User-Agent": "test"}] * 2


async def test_current_weather(weather) -> None:
    """Current temperature and condition come from the current page."""
    assert weather["current"] == {
        "condition": "cloudy",
        "condition_hu": "Erősen felhős",
        "native_temperature": 14,
        "native_temperature_unit": "°C",
        "short_forecast": "Kettősfronti hatás várható",
        "sunrise": datetime(2026, 11, 18, 6, 54, tzinfo=BUDAPEST),
        "sunset": datetime(2026, 11, 18, 16, 5, tzinfo=BUDAPEST),
    }


async def test_daily_forecast(weather) -> None:
    """The daily columns become one forecast per day with real dates."""
    daily = weather["daily_forecast"]
    assert len(daily) == 15
    assert [d["datetime"][:10] for d in daily[:2]] == ["2026-11-18", "2026-11-19"]
    # The month changes inside the forecast; the date comes from the title.
    assert daily[-1]["datetime"] == "2026-12-02T00:00:00+01:00"
    for day in daily:
        assert day["condition"] in VALID_CONDITIONS
        assert isinstance(day["temperature"], int)
        assert day["temperature"] >= day["templow"]


async def test_daily_precipitation_amounts(weather) -> None:
    """The daily rain amount is read from the "17 mm" text."""
    amounts = [d["precipitation"] for d in weather["daily_forecast"][:6]]
    assert amounts == [0.0, 17.0, 0.0, 0.0, 4.0, 0.0]


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
        assert isinstance(hour["temperature"], int)
        assert hour["wind_speed"] is not None
        assert 0 <= hour["wind_bearing"] <= 360
        assert isinstance(hour["precipitation_probability"], int)
    assert any(hour["precipitation"] > 0 for hour in hourly)


async def test_hourly_precipitation_in_tenths_of_mm(weather) -> None:
    """The "<!--34 mm-->" comments are tenths of a millimetre (issue #33)."""
    hourly = weather["hourly_forecast"]
    # 14:00-22:00 on 19 November: the comments say 7 ... 3 "mm".
    rainy = [hour["precipitation"] for hour in hourly[24:33]]
    assert rainy == [0.7, 1.2, 2.3, 3.4, 3.9, 3.2, 2.0, 0.9, 0.3]
    # The hours of that day add up to the 17 mm of the daily forecast.
    day = [h for h in hourly if h["datetime"].startswith("2026-11-19")]
    assert round(sum(h["precipitation"] for h in day), 1) == 17.9
    assert weather["daily_forecast"][1]["precipitation"] == 17.0


async def test_hourly_rain_chance_without_amount(weather) -> None:
    """Hours without an amount keep their chance of rain (issue #33)."""
    hourly = weather["hourly_forecast"]
    chances = {
        hour["datetime"]: hour["precipitation_probability"]
        for hour in hourly
        if hour["precipitation"] == 0
    }
    assert chances["2026-11-19T00:00:00+01:00"] == 30
    assert chances["2026-11-19T13:00:00+01:00"] == 22
    assert chances["2026-11-19T23:00:00+01:00"] == 50
    # Hours with no chance on the page stay at 0.
    assert chances["2026-11-18T14:00:00+01:00"] == 0


async def test_hourly_times_follow_local_time_zone(freezer) -> None:
    """Forecast times are converted to the Home Assistant time zone."""
    freezer.move_to(FIXTURE_TIME)
    data = await _fetch(FakeClientSession(), local_tz=ZoneInfo("UTC"))
    assert data["hourly_forecast"][0]["datetime"] == "2026-11-18T13:00:00+00:00"


async def test_missing_parts_do_not_break_the_update(freezer) -> None:
    """Missing sunrise, condition or a broken card only drop that value."""
    freezer.move_to(FIXTURE_TIME)
    current = _without(
        load_fixture("idojaras.html"),
        "img[src*=sunrise]",
        "img[alt=Napkelte]",
        "div.current-weather",
    )
    hourly_page = BeautifulSoup(load_fixture("elorejelzes.html"), "html.parser")
    hourly_page.select_one(".wide-hourly-forecast-card .tempBarGraph").decompose()
    session = FakeClientSession(
        {"/idojaras/": current, "/elorejelzes/": str(hourly_page)}
    )

    data = await _fetch(session)

    assert data["current"]["condition"] is None
    assert data["current"]["native_temperature"] == 14
    assert len(data["daily_forecast"]) == 15
    assert len(data["hourly_forecast"]) == 35


async def test_page_without_weather_data_fails(freezer) -> None:
    """A page without any weather data is an update error, not empty data."""
    freezer.move_to(FIXTURE_TIME)
    empty = "<html><body>Nincs ilyen település</body></html>"
    session = FakeClientSession({"/idojaras/": empty, "/elorejelzes/": empty})
    with pytest.raises(UpdateFailed):
        await _fetch(session)


def test_unknown_condition_is_none_and_logged_once(caplog, monkeypatch) -> None:
    """Unknown texts give no condition, and are logged once."""
    monkeypatch.setattr(coordinator, "_unknown_conditions", set())
    with caplog.at_level(logging.WARNING):
        assert map_condition("Teljesen új állapot") is None
        assert map_condition("teljesen  új állapot ") is None
    assert caplog.text.count("Unknown idokep.hu weather condition") == 1


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Erősen felhős\n  ", "cloudy"),
        ("ködös", "fog"),
        ("ködszitálás", "fog"),
        ("porvihar", "exceptional"),
        ("", None),
        (None, None),
    ],
)
def test_map_condition(text, expected) -> None:
    """Texts are cleaned before mapping; new texts are mapped."""
    assert map_condition(text) == expected


def test_generate_date_rolls_into_next_month() -> None:
    """A day number lower than today belongs to the next month."""
    today = date(2026, 12, 30)
    assert generate_date(31, today) == date(2026, 12, 31)
    assert generate_date(2, today) == date(2027, 1, 2)


def test_generate_date_invalid_day_returns_none() -> None:
    """A day that does not exist returns None instead of a text."""
    assert generate_date(31, date(2026, 11, 30)) is None


async def test_page_shows_which_place_idokep_used(weather) -> None:
    """The place from the page title is returned (Budapest for unknown names)."""
    assert weather["location"] == "Érd"


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Érd időjárás - Időkép", "Érd"),
        ("Budapest XI. kerület időjárás - Időkép", "Budapest XI. kerület"),
        ("Időkép", None),
    ],
)
def test_parse_location_name(title, expected) -> None:
    """The place name is the part before 'időjárás' in the title."""
    soup = BeautifulSoup(f"<title>{title}</title>", "html.parser")
    assert coordinator.parse_location_name(soup) == expected


def test_parse_location_name_without_title() -> None:
    """A page without a title gives no place name."""
    assert coordinator.parse_location_name(BeautifulSoup("", "html.parser")) is None


def _hour(start: str, condition: str) -> dict:
    return {"datetime": start, "condition": condition}


@pytest.mark.parametrize(
    ("forecast", "expected"),
    [
        # A storm in the current hour (started 30 minutes ago).
        ([_hour("2026-11-18T13:00:00+01:00", "lightning-rainy")], True),
        # A storm starting in 45 minutes.
        ([_hour("2026-11-18T14:15:00+01:00", "lightning")], True),
        # A storm in two hours is not "next hour".
        ([_hour("2026-11-18T15:30:00+01:00", "lightning")], False),
        # A storm that ended.
        ([_hour("2026-11-18T12:00:00+01:00", "lightning")], False),
        # Rain is not a storm.
        ([_hour("2026-11-18T14:00:00+01:00", "rainy")], False),
        # Broken entries are ignored.
        ([{"condition": "lightning"}, _hour("x", "lightning")], False),
    ],
)
def test_storm_expected(forecast, expected) -> None:
    """Thunderstorm within the next hour (the HA conditions, not the text)."""
    now = datetime(2026, 11, 18, 13, 30, tzinfo=BUDAPEST)
    assert storm_expected(forecast, now, timedelta(hours=1)) is expected


async def test_daily_hazard_notes(weather) -> None:
    """The "veszély" notes of the daily forecast (real data, 2026-11-18)."""
    hazards = weather["hazards"]
    assert [(h["date"], h["description"]) for h in hazards] == [
        ("2026-11-18", "Hidegfront erős széllel"),
        ("2026-11-19", "Sok eső"),
        ("2026-11-20", "Szeles nap"),
        ("2026-11-21", "Hidegfront erős széllel"),
        ("2026-11-23", "Hidegfront erős széllel"),
    ]
    assert hazards[1]["icon_url"] == (
        "https://www.idokep.hu/assets/alertIcons/nagymennyisegu_eso.png"
    )


async def test_no_alerts_on_a_calm_day(weather) -> None:
    """No coloured alert was active when the pages were saved."""
    assert weather["alerts"] == []


async def test_coloured_alerts(freezer) -> None:
    """Alert bar and hourly alerts; repeated hourly alerts count once."""
    freezer.move_to(FIXTURE_TIME)
    data = await _fetch(FakeClientSession(pages_with_alerts()))

    assert data["alerts"] == [
        {
            "level": "yellow",
            "type": "wind",
            "description": "Sárga riasztás szélre",
            "icon_url": None,
        },
        {
            "level": "orange",
            "type": "thunderstorm",
            "description": "Narancs riasztás zivatar",
            "icon_url": "https://www.idokep.hu/images/alerts/thunder.png",
        },
        {
            "level": "red",
            "type": "storm",
            "description": "Piros riasztás viharos szélre",
            "icon_url": "https://www.idokep.hu/images/alerts/storm.png",
        },
    ]


@pytest.mark.parametrize(
    ("text", "expected_type"),
    [
        ("Sárga riasztás ónos esőre", "freezing_rain"),
        ("Sárga riasztás hóra", "snow"),
        ("Narancs riasztás hőségre", "heat"),
        ("Sárga riasztás ködre", "fog"),
        ("Valami új", "general"),
    ],
)
def test_alert_types(text, expected_type) -> None:
    """The alert type comes from the Hungarian text."""
    assert coordinator._alert_type(text) == expected_type


async def test_30_day_forecast(freezer) -> None:
    """With 30 days the daily forecast comes from the 30-day page."""
    freezer.move_to(FIXTURE_TIME)
    session = FakeClientSession()

    data = await FetchWeatherData(session, "Érd", BUDAPEST, BUDAPEST, None, 30)

    daily = data["daily_forecast"]
    assert len(daily) == 30
    assert daily[0]["datetime"] == "2026-11-18T00:00:00+01:00"
    assert daily[-1]["datetime"] == "2026-12-17T00:00:00+01:00"
    # min and max close together ("min-max-close"): still max, then min.
    assert (daily[8]["temperature"], daily[8]["templow"]) == (3, 1)
    assert session.requested[-1] == "https://www.idokep.hu/30napos/Érd"


async def test_30_day_page_broken_keeps_15_days(freezer) -> None:
    """If the 30-day page can't be read, the 15-day forecast is kept."""
    freezer.move_to(FIXTURE_TIME)
    session = FakeClientSession(
        {
            "/idojaras/": load_fixture("idojaras.html"),
            "/elorejelzes/": load_fixture("elorejelzes.html"),
            "/30napos/": "<html><body>átalakítás alatt</body></html>",
        }
    )

    data = await FetchWeatherData(session, "Érd", BUDAPEST, BUDAPEST, None, 30)

    assert len(data["daily_forecast"]) == 15


async def test_15_days_downloads_two_pages(weather) -> None:
    """The default needs no extra download."""
    assert not any("/30napos/" in url for url in weather["session"].requested)
