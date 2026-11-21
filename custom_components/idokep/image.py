"""Időkép radar image platform."""

from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import get_radar_coordinator
from .const import ATTRIBUTION, RADAR_IMAGE_UNIQUE_ID
from .entity import radar_device_info
from .radar import RadarUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the latest radar image entity."""
    async_add_entities([IdokepRadarImage(hass, get_radar_coordinator(hass, entry))])


class IdokepRadarImage(CoordinatorEntity, ImageEntity):
    """The most recently downloaded Időkép radar image."""

    _attr_attribution = ATTRIBUTION
    _attr_content_type = "image/jpeg"
    _attr_has_entity_name = True
    _attr_translation_key = "latest_radar_image"

    def __init__(
        self, hass: HomeAssistant, coordinator: RadarUpdateCoordinator
    ) -> None:
        """Initialize the radar image entity."""
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)
        self._attr_unique_id = RADAR_IMAGE_UNIQUE_ID
        self._attr_device_info = radar_device_info()
        self._attr_image_last_updated = coordinator.data[-1].fetched_at

    async def async_image(self) -> bytes | None:
        """Return the latest radar JPEG."""
        return self.coordinator.data[-1].image

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update the image timestamp when a new frame arrives."""
        self._attr_image_last_updated = self.coordinator.data[-1].fetched_at
        super()._handle_coordinator_update()
