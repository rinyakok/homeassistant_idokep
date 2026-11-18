"""Shared fixtures for the Időkép integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

# The fixture pages were saved from idokep.hu for Érd at this moment.
FIXTURE_TIME = "2026-11-18T13:58:00+01:00"


def load_fixture(name: str) -> str:
    """Return a saved idokep.hu page."""
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeResponse:
    """Minimal stand-in for an aiohttp response."""

    def __init__(self, text: str) -> None:
        self._text = text

    def raise_for_status(self) -> None:
        return None

    async def text(self) -> str:
        return self._text

    async def __aenter__(self) -> FakeResponse:
        return self

    async def __aexit__(self, *exc) -> None:
        return None


class FakeClientSession:
    """Serves the saved pages instead of calling idokep.hu."""

    def __init__(self, pages: dict[str, str] | None = None) -> None:
        self.pages = pages or {
            "/idojaras/": load_fixture("idojaras.html"),
            "/elorejelzes/": load_fixture("elorejelzes.html"),
        }
        self.requested: list[str] = []
        self.headers: list[dict | None] = []

    def get(self, url: str, headers=None, timeout=None) -> FakeResponse:
        self.requested.append(url)
        self.headers.append(headers)
        for part, page in self.pages.items():
            if part in url:
                return FakeResponse(page)
        raise AssertionError(f"Unexpected URL: {url}")


@pytest.fixture(autouse=True)
def enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load this repository's integration."""
    return


@pytest.fixture
def fake_idokep(monkeypatch) -> FakeClientSession:
    """Answer idokep.hu requests from the saved pages."""
    session = FakeClientSession()
    monkeypatch.setattr(
        "custom_components.idokep.coordinator.async_get_clientsession",
        lambda hass: session,
    )
    return session
