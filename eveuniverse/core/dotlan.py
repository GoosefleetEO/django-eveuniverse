"""Generates profile URLs for dotlan."""

from enum import Enum, auto
from urllib.parse import quote, urljoin


class _Category(Enum):
    ALLIANCE = auto()
    CORPORAITON = auto()
    FACTION = auto()
    REGION = auto()
    SOLARSYSTEM = auto()


_BASE_URL = "https://evemaps.dotlan.net"


def _build_url(category: _Category, name: str) -> str:
    """URL to profile page for an eve entity."""

    partials = {
        _Category.ALLIANCE: "alliance",
        _Category.CORPORAITON: "corp",
        _Category.FACTION: "factionwarfare",
        _Category.REGION: "map",
        _Category.SOLARSYSTEM: "system",
    }
    try:
        partial = partials[category]
    except KeyError as ex:
        raise ValueError(f"Invalid category: {category}") from ex
    return urljoin(
        _BASE_URL, "{}/{}".format(partial, quote(str(name).replace(" ", "_")))
    )


def alliance_url(name: str) -> str:
    """URL for page about given alliance on dotlan."""
    return _build_url(_Category.ALLIANCE, name)


def corporation_url(name: str) -> str:
    """URL for page about given corporation on dotlan."""
    return _build_url(_Category.CORPORAITON, name)


def faction_url(name: str) -> str:
    """URL for page about given corporation on dotlan."""
    return _build_url(_Category.FACTION, name)


def region_url(name: str) -> str:
    """URL for page about given region on dotlan."""
    return _build_url(_Category.REGION, name)


def solar_system_url(name: str) -> str:
    """URL for page about given solar system on dotlan."""
    return _build_url(_Category.SOLARSYSTEM, name)
