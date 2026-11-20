"""Shared fixtures for the Időkép integration tests."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

# The fixture pages were saved from idokep.hu for Érd at this moment.
FIXTURE_TIME = "2026-11-18T13:58:00+01:00"


def load_fixture(name: str) -> str:
    """Return a saved idokep.hu page."""
    return (FIXTURES / name).read_text(encoding="utf-8")


# No coloured alert was active when the pages were saved. These snippets
# follow the alert markup that FabianGabor/HA-Idokep reads (from its tests).
ALERT_BAR = (
    '<div class="container ik alert-bar yellow p-0" id="topalertbar">'
    '<a href="/radar#riasztas"><i class="fas fa-exclamation-triangle"></i>'
    " Sárga riasztás szélre</a></div>"
)
HOURLY_ALERT = (
    '<a class="ik hover-over" data-bs-content="{text}">'
    '<img class="ik forecast-alert-icon" src="/images/alerts/{icon}.png"></a>'
)


def pages_with_alerts() -> dict[str, str]:
    """Return the saved pages with one alert bar and three hourly alerts."""
    current = load_fixture("idojaras.html").replace("<body>", f"<body>{ALERT_BAR}", 1)
    hourly = load_fixture("elorejelzes.html")
    empty_box = '<div class="ik genericHourlyAlert">\n</div>'
    for text, icon in (
        ("Narancs riasztás zivatar", "thunder"),
        ("Narancs riasztás zivatar", "thunder"),  # the next hour: same alert
        ("Piros riasztás viharos szélre", "storm"),
    ):
        box = HOURLY_ALERT.format(text=text, icon=icon)
        hourly = hourly.replace(
            empty_box, f'<div class="ik genericHourlyAlert">{box}</div>', 1
        )
    return {"/idojaras/": current, "/elorejelzes/": hourly}


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
        # With the saved Érd pages, the page title follows the requested
        # place, like on idokep.hu ("Győr időjárás - Időkép").
        self.echo_location = pages is None
        self.pages = pages or {
            "/idojaras/": load_fixture("idojaras.html"),
            "/elorejelzes/": load_fixture("elorejelzes.html"),
            "/30napos/": load_fixture("30napos.html"),
        }
        self.requested: list[str] = []
        self.headers: list[dict | None] = []
        self.error: Exception | None = None

    def get(self, url: str, headers=None, timeout=None) -> FakeResponse:
        self.requested.append(url)
        self.headers.append(headers)
        if self.error is not None:
            raise self.error
        for part, page in self.pages.items():
            if part in url:
                if self.echo_location:
                    place = unquote(url.rsplit("/", 1)[-1])
                    page = page.replace("Érd időjárás", f"{place} időjárás")
                return FakeResponse(page)
        if url.endswith("/szmog"):
            return FakeResponse(
                "<script>window.szmogTerkepek = []; "
                'window.szmogTerkepek.push({"allomasok":[]});</script>'
            )
        if url.endswith("/pollen"):
            return FakeResponse('<map name="pollen"></map>')
        raise AssertionError(f"Unexpected URL: {url}")


@pytest.fixture(autouse=True)
def enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load this repository's integration."""
    return


@pytest.fixture
def fake_idokep(monkeypatch) -> FakeClientSession:
    """Answer idokep.hu requests from the saved pages."""
    session = FakeClientSession()
    for module in ("coordinator", "config_flow"):
        monkeypatch.setattr(
            f"custom_components.idokep.{module}.async_get_clientsession",
            lambda hass: session,
        )
    return session
