"""Tests for Időkép radar image handling."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

import pytest
from homeassistant.util import dt as dt_util

from custom_components.idokep.camera import IdokepRadarCamera
from custom_components.idokep.radar import (
    RadarDataError,
    RadarFrame,
    RadarUpdateCoordinator,
    extract_radar_image_url,
)

from .conftest import FakeClientSession


def test_extract_radar_image_url() -> None:
    """Read the JPEG URL from the radar page metadata."""
    page = (
        '<meta property="og:image" '
        'content="https://www.idokep.hu/radar/radar0.jpg?123">'
    )
    assert extract_radar_image_url(page) == "https://www.idokep.hu/radar/radar0.jpg?123"


def test_reject_external_radar_image_url() -> None:
    """Do not fetch an image hosted outside idokep.hu."""
    with pytest.raises(RadarDataError):
        extract_radar_image_url(
            '<meta property="og:image" content="https://example.com/image.jpg">'
        )


async def test_radar_history_keeps_only_last_hour(
    hass, fake_idokep: FakeClientSession
) -> None:
    """Drop expired frames while adding a newly fetched JPEG."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain="idokep",
        title="Időkép radar",
        data={"radar_config_entry": True},
        unique_id="idokep-radar",
        version=2,
    )
    entry.add_to_hass(hass)
    coordinator = RadarUpdateCoordinator(hass, entry)
    now = dt_util.utcnow()
    coordinator.data = (
        RadarFrame(now - timedelta(hours=2), b"\xff\xd8old"),
        RadarFrame(now - timedelta(minutes=55), b"\xff\xd8recent"),
    )
    fake_idokep.radar_image = b"\xff\xd8new"

    frames = await coordinator._async_update_data()

    assert [frame.image for frame in frames] == [b"\xff\xd8recent", b"\xff\xd8new"]


async def test_radar_camera_cycles_through_frames() -> None:
    """Return buffered frames in order and restart at the oldest frame."""
    frames = (
        RadarFrame(dt_util.utcnow(), b"\xff\xd8first"),
        RadarFrame(dt_util.utcnow(), b"\xff\xd8second"),
    )
    camera = IdokepRadarCamera(SimpleNamespace(data=frames))

    assert await camera.async_camera_image() == b"\xff\xd8first"
    assert await camera.async_camera_image() == b"\xff\xd8second"
    assert await camera.async_camera_image() == b"\xff\xd8first"
