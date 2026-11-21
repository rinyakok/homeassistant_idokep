"""Tests for Időkép map station measurements."""

from __future__ import annotations

import json

from custom_components.idokep.coordinator import (
    FetchPollenCities,
    FetchPollenData,
    FetchPollenLocation,
    FetchSmogCities,
    FetchSmogCityData,
    FetchSmogData,
    FetchSmogStations,
    FetchStationChoices,
    FetchStationWeatherData,
)

from .conftest import FakeClientSession


def _session() -> FakeClientSession:
    """Return saved-format map data for one measurement point."""
    session = FakeClientSession()
    session.pages.update(
        {
            "/homerseklet_hu.json": json.dumps(
                {
                    "meresek": [
                        [
                            47.5,
                            19.1,
                            12.5,
                            1795198921,
                            "Érd",
                            "amator",
                            "station-7",
                            1,
                            258,
                            "Automata",
                        ]
                    ]
                }
            ),
            "/szel": (
                "<script>window.szelterkep = "
                '{"allomasok":[[47.5,19.1,180,4,6,1795198921,'
                '"Érd","Automata","station-7",0]]};</script>'
            ),
            "/csapadek": (
                "<script>(window.csapadekTerkepek = "
                "window.csapadekTerkepek || []).push("
                '{"allomasok":[[1795198921,47.5,19.1,2.4,'
                '"Érd","station-7",3.1]]});</script>'
            ),
        }
    )
    return session


async def test_station_data_matches_identifier() -> None:
    """The selected point's measurements are parsed from all three maps."""
    data = await FetchStationWeatherData(_session(), "station-7")

    assert data["temperature"]["value"] == 12.5
    assert data["temperature"]["station_name"] == "Érd"
    assert data["precipitation"]["value"] == 2.4
    assert data["precipitation"]["radar_precipitation"] == 3.1
    assert data["wind_speed"]["value"] == 4
    assert data["wind_speed"]["wind_direction_degrees"] == 180
    assert data["wind_gust"]["value"] == 6
    assert data["wind_gust"]["measured_at"] == "2026-11-20T18:22:01+00:00"


async def test_station_data_matches_accentless_name() -> None:
    """Station names match regardless of accents or letter case."""
    data = await FetchStationWeatherData(_session(), "erd")

    assert data["temperature"]["value"] == 12.5
    assert data["wind_speed"]["value"] == 4


async def test_station_data_missing_measurement_is_none() -> None:
    """A point without a measurement in one map has no value for that sensor."""
    session = _session()
    session.pages["/csapadek"] = (
        "<script>(window.csapadekTerkepek = "
        "window.csapadekTerkepek || []).push("
        '{"allomasok":[[1795198921,47.5,19.1,2.4,"Another place","other",3.1]]});'
        "</script>"
    )

    data = await FetchStationWeatherData(session, "station-7")

    assert data["temperature"]["value"] == 12.5
    assert data["precipitation"] is None


async def test_station_choices_are_deduplicated_across_maps() -> None:
    """The selector lists a map station once, regardless of available maps."""
    stations = await FetchStationChoices(_session())

    assert stations == [{"id": "station-7", "name": "Érd"}]


def _smog_page() -> str:
    """Return two map views with duplicate and distinct station rows."""
    stations = (
        '["erd-1",47.5,19.1,"Érd","Érd",1795198921,52,18,"OLM"],'
        '["bud-1",47.5,19.1,"Budapest","Budapest XI.",1795198921,21,null,"OLM"]'
    )
    return (
        "<script>window.szmogTerkepek = [];"
        f'window.szmogTerkepek.push({{"allomasok":[{stations}]}});'
        f'window.szmogTerkepek.push({{"allomasok":[{stations}]}});'
        "</script>"
    )


async def test_smog_lookup_ignores_case_but_preserves_accents() -> None:
    """The location match is case-insensitive, not accent-insensitive."""
    session = FakeClientSession({"/szmog": _smog_page()})

    stations = await FetchSmogStations(session, "ÉRD")
    accentless = await FetchSmogStations(session, "erd")

    assert [station["id"] for station in stations] == ["erd-1"]
    assert stations[0]["has_pm25"] is True
    assert accentless == []


async def test_smog_data_is_deduplicated_and_contains_measurements() -> None:
    """Both map views collapse to one current observation per station ID."""
    session = FakeClientSession({"/szmog": _smog_page()})

    data = await FetchSmogData(session, ["erd-1", "bud-1"])

    assert data["erd-1"]["pm10"] == 52
    assert data["erd-1"]["pm25"] == 18
    assert data["erd-1"]["source"] == "OLM"
    assert data["bud-1"]["pm10"] == 21
    assert data["bud-1"]["pm25"] is None


async def test_smog_cities_are_sorted_and_city_data_is_filtered() -> None:
    """The city selector lists available cities and fetches only the selected one."""
    session = FakeClientSession({"/szmog": _smog_page()})

    cities = await FetchSmogCities(session)
    data = await FetchSmogCityData(session, "Érd")

    assert cities == ["Budapest", "Érd"]
    assert list(data) == ["erd-1"]


def _pollen_page() -> str:
    """Return image-map tooltips for one data location and one empty location."""
    return (
        '<map name="pollen">'
        "<area onmouseover='Tip(\"<strong>Érd</strong><br/>"
        "<font>Pázsitfűfélék: alacsony</font><br/>"
        "<font>Parlagfű: nincs</font>\")'>"
        "<area onmouseover='Tip(\"<strong>Szekszárd</strong><br/>\")'>"
        "</map>"
    )


async def test_pollen_lookup_matches_case_but_preserves_accents() -> None:
    """Pollen map location matching is case-insensitive and accent-sensitive."""
    session = FakeClientSession({"/pollen": _pollen_page()})

    match = await FetchPollenLocation(session, "ÉRD")
    accentless = await FetchPollenLocation(session, "erd")
    no_measurements = await FetchPollenLocation(session, "Szekszárd")

    assert match == {
        "city": "Érd",
        "values": {"grass": "alacsony", "ragweed": "nincs"},
    }
    assert accentless is None
    assert no_measurements is None


async def test_pollen_data_returns_only_qualitative_levels() -> None:
    """Pollen values are read as the categories and levels shown in tooltips."""
    session = FakeClientSession({"/pollen": _pollen_page()})

    data = await FetchPollenData(session, "Érd")

    assert data == {"grass": "alacsony", "ragweed": "nincs"}


async def test_pollen_cities_exclude_locations_without_values() -> None:
    """Only cities with current pollen readings can be selected."""
    session = FakeClientSession({"/pollen": _pollen_page()})

    assert await FetchPollenCities(session) == ["Érd"]
