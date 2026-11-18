"""Shared fixtures for the Időkép integration tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

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

    async def text(self) -> str:
        return self._text

    async def __aenter__(self) -> FakeResponse:
        return self

    async def __aexit__(self, *exc) -> None:
        return None


class FakeClientSession:
    """Serves the saved pages instead of calling idokep.hu."""

    pages = {
        "/idojaras/": "idojaras.html",
        "/elorejelzes/": "elorejelzes.html",
    }
    requested: list[str] = []

    def __init__(self, *args, **kwargs) -> None:
        self.headers = kwargs.get("headers")

    def get(self, url: str) -> FakeResponse:
        FakeClientSession.requested.append(url)
        for part, fixture in self.pages.items():
            if part in url:
                return FakeResponse(load_fixture(fixture))
        raise AssertionError(f"Unexpected URL: {url}")

    async def __aenter__(self) -> FakeClientSession:
        return self

    async def __aexit__(self, *exc) -> None:
        return None


@pytest.fixture(autouse=True)
def enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load this repository's integration."""
    return


@pytest.fixture
def fake_idokep(monkeypatch):
    """Answer idokep.hu requests from the saved pages."""
    FakeClientSession.requested = []
    # Replace only the integration's view of aiohttp, not the real module,
    # so Home Assistant itself keeps its normal HTTP client.
    monkeypatch.setattr(
        "custom_components.idokep.coordinator.aiohttp",
        SimpleNamespace(ClientSession=FakeClientSession),
    )
    return FakeClientSession
