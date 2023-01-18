"""Wrapper to access evesdeapi."""

from dataclasses import dataclass
from typing import Optional

import requests

from django.core.cache import cache
from eveuniverse.helpers import dict_hash

_CACHE_TIMEOUT = 3_600 * 12
_BASE_URL = "https://evesdeapi.kalkoken.net/latest"


@dataclass
class EveItem:
    """A celestial item."""

    id: int
    name: str
    type_id: int
    distance: float

    @classmethod
    def from_dict(cls, record: dict) -> "EveItem":
        return cls(
            id=int(record["item_id"]),
            name=str(record["name"]),
            type_id=int(record["type_id"]),
            distance=float(record["distance"]),
        )


def nearest_celestial(
    solar_system_id: float, x: float, y: float, z: float, group_id: int = None
) -> Optional[EveItem]:
    """Fetch nearest celestial to given coordinates from API. Results are cached.

    Args:
        solar_system_id: Eve ID of solar system
        x, y, z: Start point in space to look from
        group_id: Eve ID of group to filter results by

    Raises:
        HTTPError: If an HTTP error is encountered

    Returns:
        Found Eve item or None if nothing found nearby.
    """
    result = _fetch_items_from_endpoint_cached(
        solar_system_id=solar_system_id, x=x, y=y, z=z, group_id=group_id
    )
    if not result:
        return None
    return EveItem.from_dict(result[0])


def _fetch_items_from_endpoint_cached(
    solar_system_id: float, x: float, y: float, z: float, group_id: int = None
) -> Optional[dict]:
    """Fetch items from endpoint with caching.

    Returns None if data from API does not have expected structure.
    """
    params = {"x": x, "y": y, "z": z}
    if group_id is not None:
        params["group_id"] = int(group_id)
    cache_key = f"eveuniverse_nearest_celestial_{dict_hash(params)}"
    result = cache.get(key=cache_key)
    if not result:
        r = requests.get(
            f"{_BASE_URL}/universe/systems/{solar_system_id}/nearest_celestials",
            params=params,
        )
        r.raise_for_status()
        result = r.json()
        cache.set(key=cache_key, value=result, timeout=_CACHE_TIMEOUT)
    return result
