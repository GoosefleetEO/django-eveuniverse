import logging
from typing import Iterable, List

from celery import shared_task
from celery_once import QueueOnce as BaseQueueOnce
from django.db.utils import OperationalError

from . import __title__, models
from .app_settings import (
    EVEUNIVERSE_LOAD_ASTEROID_BELTS,
    EVEUNIVERSE_LOAD_DOGMAS,
    EVEUNIVERSE_LOAD_GRAPHICS,
    EVEUNIVERSE_LOAD_MARKET_GROUPS,
    EVEUNIVERSE_LOAD_MOONS,
    EVEUNIVERSE_LOAD_PLANETS,
    EVEUNIVERSE_LOAD_STARGATES,
    EVEUNIVERSE_LOAD_STARS,
    EVEUNIVERSE_LOAD_STATIONS,
    EVEUNIVERSE_LOAD_TYPE_MATERIALS,
    EVEUNIVERSE_TASKS_TIME_LIMIT,
)
from .constants import POST_UNIVERSE_NAMES_MAX_ITEMS, EveCategoryId
from .models import EveEntity, EveMarketPrice, EveUniverseEntityModel
from .providers import esi
from .utils import LoggerAddTag, chunks

logger = LoggerAddTag(logging.getLogger(__name__), __title__)
# logging.getLogger("esi").setLevel(logging.INFO)


class QueueOnce(BaseQueueOnce):
    """Make sure all redundant tasks will abort gracefully."""

    once = BaseQueueOnce.once
    once["graceful"] = True


# params for all tasks
TASK_DEFAULTS = {"time_limit": EVEUNIVERSE_TASKS_TIME_LIMIT}

# params for tasks that make ESI calls
TASK_ESI_DEFAULTS = {
    **TASK_DEFAULTS,
    **{
        "autoretry_for": [OperationalError],
        "retry_kwargs": {"max_retries": 3},
        "retry_backoff": True,
    },
}
TASK_ESI_DEFAULTS_ONCE = {**TASK_ESI_DEFAULTS, **{"base": QueueOnce}}


# Eve Universe objects


@shared_task(**TASK_ESI_DEFAULTS_ONCE)
def load_eve_object(
    model_name: str, id: int, include_children=False, wait_for_children=True
) -> None:
    """Task for loading an eve object.
    Will only be created from ESI if it does not exist
    """
    logger.info("Loading %s with ID %s", model_name, id)
    ModelClass = EveUniverseEntityModel.get_model_class(model_name)
    ModelClass.objects.get_or_create_esi(
        id=id, include_children=include_children, wait_for_children=wait_for_children
    )


@shared_task(**TASK_ESI_DEFAULTS_ONCE)
def update_or_create_eve_object(
    model_name: str,
    id: int,
    include_children=False,
    wait_for_children=True,
    enabled_sections: List[str] = None,
) -> None:
    """Update or create an eve object from ESI.

    Args:
        model_name: Name of the respective Django model, e.g. ``"EveType"``
        id: Eve Online ID of object
        include_children: if child objects should be updated/created as well (only when a new object is created)
        wait_for_children: when true child objects will be updated/created blocking (if any), else async (only when a new object is created)
        enabled_sections: Sections to load regardless of current settings, e.g. `[EveType.Section.DOGMAS]` will always load dogmas for EveTypes
    """
    logger.info("Updating/Creating %s with ID %s", model_name, id)
    ModelClass = EveUniverseEntityModel.get_model_class(model_name)
    ModelClass.objects.update_or_create_esi(
        id=id,
        include_children=include_children,
        wait_for_children=wait_for_children,
        enabled_sections=enabled_sections,
    )


@shared_task(**TASK_ESI_DEFAULTS_ONCE)
def update_or_create_inline_object(
    parent_obj_id: int,
    parent_fk: str,
    eve_data_obj: dict,
    other_pk_info: dict,
    parent2_model_name: str,
    inline_model_name: str,
    parent_model_name: str,
    enabled_sections: List[str] = None,
) -> None:
    """Task for updating or creating a single inline object from ESI"""
    logger.info(
        "Updating/Creating inline object %s for %s wit ID %s",
        inline_model_name,
        parent_model_name,
        parent_obj_id,
    )
    ModelClass = EveUniverseEntityModel.get_model_class(parent_model_name)
    ModelClass.objects._update_or_create_inline_object(
        parent_obj_id=parent_obj_id,
        parent_fk=parent_fk,
        eve_data_obj=eve_data_obj,
        other_pk_info=other_pk_info,
        parent2_model_name=parent2_model_name,
        inline_model_name=inline_model_name,
        enabled_sections=enabled_sections,
    )


# EveEntity objects


@shared_task(**TASK_ESI_DEFAULTS)
def create_eve_entities(ids: Iterable[int]) -> None:
    """Task for bulk creating and resolving multiple entities from ESI."""
    EveEntity.objects.bulk_create_esi(ids)


@shared_task(**TASK_ESI_DEFAULTS_ONCE)
def update_unresolved_eve_entities() -> None:
    """Update all unresolved EveEntity objects from ESI.

    Will resolve entities in parallel to speed up resolving large sets.
    """
    ids = list(EveEntity.objects.filter(name="").valid_ids())
    logger.info("Updating %d unresolved entities from ESI", len(ids))
    for chunk_ids in chunks(ids, POST_UNIVERSE_NAMES_MAX_ITEMS):
        _update_unresolved_eve_entities_for_page.delay(chunk_ids)


@shared_task(**TASK_ESI_DEFAULTS)
def _update_unresolved_eve_entities_for_page(ids: Iterable[int]) -> None:
    """Update unresolved EveEntity objects for given ids from ESI."""
    EveEntity.objects.update_from_esi_by_id(ids)


# Object loaders


def _eve_object_names_to_be_loaded() -> list:
    """returns a list of eve object that are loaded"""
    config_map = [
        (EVEUNIVERSE_LOAD_ASTEROID_BELTS, "asteroid belts"),
        (EVEUNIVERSE_LOAD_DOGMAS, "dogmas"),
        (EVEUNIVERSE_LOAD_GRAPHICS, "graphics"),
        (EVEUNIVERSE_LOAD_MARKET_GROUPS, "market groups"),
        (EVEUNIVERSE_LOAD_MOONS, "moons"),
        (EVEUNIVERSE_LOAD_PLANETS, "planets"),
        (EVEUNIVERSE_LOAD_STARGATES, "stargates"),
        (EVEUNIVERSE_LOAD_STARS, "stars"),
        (EVEUNIVERSE_LOAD_STATIONS, "stations"),
        (EVEUNIVERSE_LOAD_TYPE_MATERIALS, "type materials"),
    ]
    names_to_be_loaded = []
    for setting, entity_name in config_map:
        if setting:
            names_to_be_loaded.append(entity_name)
    return sorted(names_to_be_loaded)


@shared_task(**TASK_ESI_DEFAULTS_ONCE)
def load_map() -> None:
    """Load the complete Eve map with all regions, constellation and solar systems
    and additional related entities if they are enabled.
    """
    logger.info(
        "Loading complete map with all regions, constellations, solar systems "
        "and the following additional entities if related to the map: %s",
        ", ".join(_eve_object_names_to_be_loaded()),
    )
    category, method = models.EveRegion._esi_path_list()
    all_ids = getattr(getattr(esi.client, category), method)().results()
    for id in all_ids:
        update_or_create_eve_object.delay(
            model_name="EveRegion",
            id=id,
            include_children=True,
            wait_for_children=False,
        )


@shared_task(**TASK_ESI_DEFAULTS_ONCE)
def load_all_types(enabled_sections: List[str] = None) -> None:
    """Load all eve types.

    Args:
        enabled_sections: Sections to load regardless of current settings
    """
    logger.info(
        "Loading all eve types from ESI plus potentially these additional objects: %s",
        ", ".join(_eve_object_names_to_be_loaded()),
    )
    category, method = models.EveCategory._esi_path_list()
    result = getattr(getattr(esi.client, category), method)().results()
    if not result:
        raise ValueError("Did not receive category IDs from ESI.")
    category_ids = sorted(result)
    logger.debug("Fetching categories for IDs: %s", category_ids)
    for category_id in category_ids:
        update_or_create_eve_object.delay(
            model_name="EveCategory",
            id=category_id,
            include_children=True,
            wait_for_children=False,
            enabled_sections=enabled_sections,
        )


def _load_category(category_id: int, force_loading_dogma: bool = False) -> None:
    """Starts a task for loading a category incl. all it's children from ESI via"""
    enabled_sections = (
        [EveUniverseEntityModel.LOAD_DOGMAS] if force_loading_dogma else None
    )
    update_or_create_eve_object.delay(
        model_name="EveCategory",
        id=category_id,
        include_children=True,
        wait_for_children=False,
        enabled_sections=enabled_sections,
    )


def _load_group(group_id: int, force_loading_dogma: bool = False) -> None:
    """Starts a task for loading a group incl. all it's children from ESI"""
    enabled_sections = (
        [EveUniverseEntityModel.LOAD_DOGMAS] if force_loading_dogma else None
    )
    update_or_create_eve_object.delay(
        model_name="EveGroup",
        id=group_id,
        include_children=True,
        wait_for_children=False,
        enabled_sections=enabled_sections,
    )


def _load_type(type_id: int, force_loading_dogma: bool = False) -> None:
    """Starts a task for loading a type incl. all it's children from ESI"""
    enabled_sections = (
        [EveUniverseEntityModel.LOAD_DOGMAS] if force_loading_dogma else None
    )
    update_or_create_eve_object.delay(
        model_name="EveType",
        id=type_id,
        include_children=False,
        wait_for_children=False,
        enabled_sections=enabled_sections,
    )


@shared_task(**TASK_ESI_DEFAULTS_ONCE)
def load_ship_types() -> None:
    """Loads all ship types"""
    logger.info("Started loading all ship types into eveuniverse")
    _load_category(EveCategoryId.SHIP.value)


@shared_task(**TASK_ESI_DEFAULTS_ONCE)
def load_structure_types() -> None:
    """Loads all structure types"""
    logger.info("Started loading all structure types into eveuniverse")
    _load_category(EveCategoryId.STRUCTURE.value)


@shared_task(**TASK_ESI_DEFAULTS_ONCE)
def load_eve_types(
    category_ids: List[int] = None,
    group_ids: List[int] = None,
    type_ids: List[int] = None,
    force_loading_dogma: bool = False,
) -> None:
    """Load specified eve types from ESI. Will always load all children except for EveType

    Args:
    - category_ids: EveCategory IDs
    - group_ids: EveGroup IDs
    - type_ids: EveType IDs
    - load_dogma: When True will load dogma for all types
    """
    logger.info("Started loading several eve types into eveuniverse")
    if category_ids:
        for category_id in category_ids:
            _load_category(category_id, force_loading_dogma)

    if group_ids:
        for group_id in group_ids:
            _load_group(group_id, force_loading_dogma)

    if type_ids:
        for type_id in type_ids:
            _load_type(type_id, force_loading_dogma)


@shared_task(**TASK_ESI_DEFAULTS_ONCE)
def update_market_prices(minutes_until_stale: int = None):
    """Updates market prices from ESI.
    see EveMarketPrice.objects.update_from_esi() for details"""
    EveMarketPrice.objects.update_from_esi(minutes_until_stale)
