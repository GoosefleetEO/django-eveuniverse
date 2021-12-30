"""Wrapper to access evemicros API"""
from collections import namedtuple
from typing import Optional
from urllib.parse import urlencode

import requests

from django.core.cache import cache

_CACHE_TIMEOUT = 3_600 * 12
_BASE_URL = "https://www.kalkoken.org/apps/evemicros/eveUniverse.php"

EveItem = namedtuple("EveItem", ["id", "name", "type_id", "distance"])


def nearest_celestial(
    x: int, y: int, z: int, solar_system_id: int
) -> Optional[EveItem]:
    """Fetch nearest celestial to given coordinates from API.

    Results are cached.

    Raises:
        HTTPError: If an HTTP error is encountered

    Returns:
        Found Eve item or None if nothing found nearby.
    """
    params = map(str, map(int, [solar_system_id, x, y, z]))
    query = urlencode({"nearestCelestials": ",".join(params)})
    item = cache.get(key=_build_cache_key(query))
    if not item:
        item = _fetch_from_api(query)
        if item is None:
            return None
    result = EveItem(
        id=int(item["itemID"]),
        name=str(item["itemName"]),
        type_id=int(item["typeID"]),
        distance=float(item["distanceKm"]),
    )
    return result


def _build_cache_key(query) -> str:
    cache_key_base = "EVEUNIVERSE_NEAREST_CELESTIAL"
    cache_key = f"{cache_key_base}_{query}"
    return cache_key


def _fetch_from_api(query) -> Optional[dict]:
    r = requests.get(f"{_BASE_URL}?{query}")
    r.raise_for_status()
    data = r.json()
    if "ok" not in data or not data["ok"] or "result" not in data or not data["result"]:
        return None
    item = data["result"][0]
    cache.set(key=_build_cache_key(query), value=item, timeout=_CACHE_TIMEOUT)
    return item
