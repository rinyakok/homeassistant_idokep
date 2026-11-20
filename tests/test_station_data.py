"""Tests for Időkép map station measurements."""

from __future__ import annotations

import json

from custom_components.idokep.coordinator import FetchStationWeatherData

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
