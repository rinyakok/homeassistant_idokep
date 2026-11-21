"""Coordinator for Időkép radar images."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlsplit

import aiohttp
from bs4 import BeautifulSoup
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import BASE_IDOKEP_URL, DOMAIN
from .coordinator import REQUEST_TIMEOUT, async_request_headers

_LOGGER = logging.getLogger(__name__)

RADAR_PAGE_URL = f"{BASE_IDOKEP_URL}/radar"
RADAR_UPDATE_INTERVAL = timedelta(minutes=5)
RADAR_HISTORY = timedelta(hours=1)
MAX_RADAR_FRAMES = 13


@dataclass(frozen=True)
class RadarFrame:
    """A downloaded radar image and its fetch time."""

    fetched_at: datetime
    image: bytes


class RadarDataError(ValueError):
    """The radar page does not contain a valid image URL."""


def extract_radar_image_url(page: str) -> str:
    """Extract the same-site JPEG URL from the radar page's Open Graph metadata."""
    meta = BeautifulSoup(page, "html.parser").find(
        "meta", attrs={"property": "og:image"}
    )
    image_url = meta.get("content") if meta else None
    if not isinstance(image_url, str) or not image_url:
        raise RadarDataError("The radar page has no og:image URL")

    try:
        image_url = urljoin(RADAR_PAGE_URL, image_url)
        parsed_url = urlsplit(image_url)
    except ValueError as err:
        raise RadarDataError("The radar image URL is invalid") from err
    if (
        parsed_url.scheme != "https"
        or parsed_url.netloc.lower() != "www.idokep.hu"
        or not parsed_url.path.startswith("/radar/")
        or not parsed_url.path.lower().endswith((".jpg", ".jpeg"))
    ):
        raise RadarDataError("The radar image URL is not a same-site JPEG")
    return image_url


class RadarUpdateCoordinator(DataUpdateCoordinator):
    """Download and retain up to one hour of Időkép radar frames."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the radar coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN} radar",
            config_entry=entry,
            update_interval=RADAR_UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> tuple[RadarFrame, ...]:
        """Fetch the latest JPEG and retain distinct frames from the last hour."""
        session = async_get_clientsession(self.hass)
        headers = await async_request_headers(self.hass)
        try:
            async with session.get(
                RADAR_PAGE_URL, headers=headers, timeout=REQUEST_TIMEOUT
            ) as response:
                response.raise_for_status()
                image_url = extract_radar_image_url(await response.text())

            async with session.get(
                image_url, headers=headers, timeout=REQUEST_TIMEOUT
            ) as response:
                response.raise_for_status()
                image = await response.read()
        except (aiohttp.ClientError, TimeoutError, RadarDataError) as err:
            raise UpdateFailed(
                f"Unable to fetch the Időkép radar image: {err}"
            ) from err

        if not image.startswith(b"\xff\xd8"):
            raise UpdateFailed("The Időkép radar response is not a JPEG image")

        now = dt_util.utcnow()
        frames = [
            frame
            for frame in self.data or ()
            if frame.fetched_at >= now - RADAR_HISTORY
        ]
        if not frames or frames[-1].image != image:
            frames.append(RadarFrame(now, image))
        return tuple(frames[-MAX_RADAR_FRAMES:])
