"""Időkép radar camera platform."""

from __future__ import annotations

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import get_radar_coordinator
from .const import ATTRIBUTION, RADAR_CAMERA_UNIQUE_ID
from .entity import radar_device_info
from .radar import RadarUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the radar image stream camera."""
    async_add_entities([IdokepRadarCamera(get_radar_coordinator(hass, entry))])


class IdokepRadarCamera(CoordinatorEntity, Camera):
    """Cycle through radar JPEGs captured during the previous hour."""

    _attr_attribution = ATTRIBUTION
    _attr_frame_interval = 0.5
    _attr_has_entity_name = True
    _attr_translation_key = "radar_image_stream"

    def __init__(self, coordinator: RadarUpdateCoordinator) -> None:
        """Initialize the radar stream camera."""
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._attr_unique_id = RADAR_CAMERA_UNIQUE_ID
        self._attr_device_info = radar_device_info()
        self._frame_index = -1

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the next JPEG in the retained radar sequence."""
        frames = self.coordinator.data
        if not frames:
            return None
        self._frame_index = (self._frame_index + 1) % len(frames)
        return frames[self._frame_index].image
