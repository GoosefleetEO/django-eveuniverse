"""Generates profile URLs for evewho."""
from enum import Enum, auto
from urllib.parse import urljoin


class _Category(Enum):
    ALLIANCE = auto()
    CHARACTER = auto()
    CORPORAITON = auto()


_BASE_URL = "https://evewho.com"


def _build_url(category: str, eve_id: int) -> str:
    """URL to profile page for an eve entity."""

    partials = {
        _Category.ALLIANCE: "alliance",
        _Category.CHARACTER: "character",
        _Category.CORPORAITON: "corporation",
    }
    try:
        partial = partials[category]
    except KeyError as ex:
        raise ValueError(f"Invalid category: {category}") from ex
    return urljoin(_BASE_URL, f"{partial}/{int(eve_id)}")


def alliance_url(eve_id: int) -> str:
    """URL for page about given alliance on evewho."""
    return _build_url(_Category.ALLIANCE, eve_id)


def character_url(eve_id: int) -> str:
    """URL for page about given character on evewho."""
    return _build_url(_Category.CHARACTER, eve_id)


def corporation_url(eve_id: int) -> str:
    """URL for page about given corporation on evewho."""
    return _build_url(_Category.CORPORAITON, eve_id)
