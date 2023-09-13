"""Managers and Querysets for Eve universe models."""


import datetime as dt
import logging
from collections import namedtuple
from typing import Any, Dict, Iterable, Optional, Tuple

from bravado.exception import HTTPNotFound
from django.db import models, transaction
from django.utils.timezone import now

from eveuniverse import __title__
from eveuniverse.app_settings import EVEUNIVERSE_BULK_METHODS_BATCH_SIZE
from eveuniverse.helpers import get_or_create_esi_or_none
from eveuniverse.providers import esi
from eveuniverse.utils import LoggerAddTag

logger = LoggerAddTag(logging.getLogger(__name__), __title__)

_FakeResponse = namedtuple("_FakeResponse", ["status_code"])


class EveUniverseEntityModelManager(models.Manager):
    """Custom manager adding the ability to fetch objects from ESI."""

    def get_or_create_esi(
        self,
        *,
        id: int,
        include_children: bool = False,
        wait_for_children: bool = True,
        enabled_sections: Optional[Iterable[str]] = None,
        task_priority: Optional[int] = None,
    ) -> Tuple[Any, bool]:
        """gets or creates an eve universe object.

        The object is automatically fetched from ESI if it does not exist (blocking).
        Will always get/create parent objects.

        Args:
            id: Eve Online ID of object
            include_children: if child objects should be updated/created as well
            (only when a new object is created)
            wait_for_children: when true child objects will be updated/created blocking
            (if any), else async (only when a new object is created)
            enabled_sections: Sections to load regardless of current settings,
            e.g. `[EveType.Section.DOGMAS]` will always load dogmas for EveTypes
            task_priority: priority of started tasks

        Returns:
            A tuple consisting of the requested object and a created flag
        """
        from eveuniverse.models import determine_effective_sections

        id = int(id)
        effective_sections = determine_effective_sections(enabled_sections)
        try:
            enabled_sections_filter = self._enabled_sections_filter(effective_sections)
            obj = self.filter(**enabled_sections_filter).get(id=id)
            return obj, False
        except self.model.DoesNotExist:
            return self.update_or_create_esi(
                id=id,
                include_children=include_children,
                wait_for_children=wait_for_children,
                enabled_sections=effective_sections,
                task_priority=task_priority,
            )

    def _enabled_sections_filter(self, enabled_sections: Iterable[str]) -> dict:
        return {
            "enabled_sections": getattr(self.model.enabled_sections, section)
            for section in enabled_sections
            if str(section) in self.model.Section.values()
        }

    def update_or_create_esi(
        self,
        *,
        id: int,
        include_children: bool = False,
        wait_for_children: bool = True,
        enabled_sections: Optional[Iterable[str]] = None,
        task_priority: Optional[int] = None,
    ) -> Tuple[Any, bool]:
        """updates or creates an Eve universe object by fetching it from ESI (blocking).
        Will always get/create parent objects

        Args:
            id: Eve Online ID of object
            include_children: if child objects should be updated/created as well (if any)
            wait_for_children: when true child objects will be updated/created blocking
            (if any), else async
            enabled_sections: Sections to load regardless of current settings,
            e.g. `[EveType.Section.DOGMAS]` will always load dogmas for EveTypes
            task_priority: priority of started tasks

        Returns:
            A tuple consisting of the requested object and a created flag
        """
        from eveuniverse.models import determine_effective_sections

        id = int(id)
        effective_sections = determine_effective_sections(enabled_sections)
        eve_data_obj = self._transform_esi_response_for_list_endpoints(
            self.model, id, self._fetch_from_esi(id=id)
        )
        if eve_data_obj:
            defaults = self.model._defaults_from_esi_obj(
                eve_data_obj, effective_sections
            )
            obj, created = self.update_or_create(id=id, defaults=defaults)
            if effective_sections and hasattr(obj, "enabled_sections"):
                updated_sections = False
                for section in effective_sections:
                    if str(section) in self.model.Section.values():
                        setattr(obj.enabled_sections, section, True)
                        updated_sections = True
                if updated_sections:
                    obj.save()

            self.model.update_or_create_inline_objects(
                parent_eve_data_obj=eve_data_obj,
                parent_obj=obj,
                wait_for_children=wait_for_children,
                enabled_sections=effective_sections,
                task_priority=task_priority,
            )

            if include_children:
                self.model.update_or_create_children(
                    parent_eve_data_obj=eve_data_obj,
                    include_children=include_children,
                    wait_for_children=wait_for_children,
                    enabled_sections=effective_sections,
                    task_priority=task_priority,
                )
        else:
            raise HTTPNotFound(
                _FakeResponse(status_code=404),  # type: ignore
                message=f"{self.model.__name__} object with id {id} not found",
            )
        return obj, created

    @staticmethod
    def _transform_esi_response_for_list_endpoints(
        model_class, id: int, esi_data
    ) -> dict:
        """Transforms raw ESI response from list endpoints if this is one
        else just passes the ESI response through
        """
        if not model_class._is_list_only_endpoint():
            return esi_data

        esi_pk = model_class._esi_pk()
        for row in esi_data:
            if esi_pk in row and row[esi_pk] == id:
                return row

        raise HTTPNotFound(
            _FakeResponse(status_code=404),  # type: ignore
            message=f"{model_class.__name__} object with id {id} not found",
        )

    def _fetch_from_esi(
        self,
        id: Optional[int] = None,
        _enabled_sections: Optional[Iterable[str]] = None,
    ) -> dict:
        """make request to ESI and return response data.
        Can handle raw ESI response from both list and normal endpoints.
        """
        if id is not None and not self.model._is_list_only_endpoint():
            params = {self.model._esi_pk(): id}
        else:
            params = {}
        category, method = self.model._esi_path_object()
        esi_data = getattr(getattr(esi.client, category), method)(**params).results()
        return esi_data

    def update_or_create_all_esi(
        self,
        *,
        include_children: bool = False,
        wait_for_children: bool = True,
        enabled_sections: Optional[Iterable[str]] = None,
        task_priority: Optional[int] = None,
    ) -> None:
        """Update or create all objects of this class from ESI.

        Loading all objects can take a long time. Use with care!

        Args:
            include_children: if child objects should be updated/created as well (if any)
            wait_for_children: when false all objects will be loaded async, else blocking
            enabled_sections: Sections to load regardless of current settings
        """
        from eveuniverse.models import determine_effective_sections
        from eveuniverse.tasks import (
            update_or_create_eve_object as task_update_or_create_eve_object,
        )

        effective_sections = determine_effective_sections(enabled_sections)

        if self.model._is_list_only_endpoint():
            self._update_or_create_all_esi_list_endpoint(effective_sections)

        else:
            self._update_or_create_all_esi_normal(
                include_children,
                wait_for_children,
                task_priority,
                task_update_or_create_eve_object,
                effective_sections,
            )

    def _update_or_create_all_esi_list_endpoint(self, effective_sections):
        esi_pk = self.model._esi_pk()
        for eve_data_obj in self._fetch_from_esi():
            params = {
                "id": eve_data_obj[esi_pk],
                "defaults": self.model._defaults_from_esi_obj(
                    eve_data_obj=eve_data_obj, enabled_sections=effective_sections
                ),
            }
            self.update_or_create(**params)

    def _update_or_create_all_esi_normal(
        self,
        include_children,
        wait_for_children,
        task_priority,
        task_update_or_create_eve_object,
        effective_sections,
    ):
        if self.model._has_esi_path_list():
            category, method = self.model._esi_path_list()
            ids = getattr(getattr(esi.client, category), method)().results()
            for id in ids:
                if wait_for_children:
                    self.update_or_create_esi(
                        id=id,
                        include_children=include_children,
                        wait_for_children=wait_for_children,
                        enabled_sections=effective_sections,
                    )
                else:
                    params: Dict[str, Any] = {
                        "kwargs": {
                            "model_name": self.model.__name__,
                            "id": id,
                            "include_children": include_children,
                            "wait_for_children": wait_for_children,
                            "enabled_sections": list(effective_sections),
                            "task_priority": task_priority,
                        },
                    }
                    if task_priority:
                        params["priority"] = task_priority
                    task_update_or_create_eve_object.apply_async(**params)  # type: ignore

        else:
            raise TypeError(
                f"ESI does not provide a list endpoint for {self.model.__name__}"
            )

    def bulk_get_or_create_esi(
        self,
        *,
        ids: Iterable[int],
        include_children: bool = False,
        wait_for_children: bool = True,
        enabled_sections: Optional[Iterable[str]] = None,
        task_priority: Optional[int] = None,
    ) -> models.QuerySet:
        """Gets or creates objects in bulk.

        Nonexisting objects will be fetched from ESI (blocking).
        Will always get/create parent objects.

        Args:
            ids: List of valid IDs of Eve objects
            include_children: when needed to updated/created if child objects should be updated/created as well (if any)
            wait_for_children: when true child objects will be updated/created blocking (if any), else async
            enabled_sections: Sections to load regardless of current settings

        Returns:
            Queryset with all requested eve objects
        """
        from eveuniverse.models import determine_effective_sections

        ids = set(map(int, ids))
        effective_sections = determine_effective_sections(enabled_sections)
        enabled_sections_filter = self._enabled_sections_filter(effective_sections)
        existing_ids = set(
            self.filter(id__in=ids)
            .filter(**enabled_sections_filter)
            .values_list("id", flat=True)
        )
        for id in ids.difference(existing_ids):
            self.update_or_create_esi(
                id=int(id),
                include_children=include_children,
                wait_for_children=wait_for_children,
                enabled_sections=effective_sections,
                task_priority=task_priority,
            )

        return self.filter(id__in=ids)


class EvePlanetManager(EveUniverseEntityModelManager):
    """:meta private:"""

    def _fetch_from_esi(
        self, id: Optional[int] = None, enabled_sections: Optional[Iterable[str]] = None
    ) -> dict:
        from eveuniverse.models import EveSolarSystem

        if id is None:
            raise ValueError("id not defined")

        esi_data = super()._fetch_from_esi(id=id)
        # no need to proceed if all children have been disabled
        if not self.model._children(enabled_sections):
            return esi_data

        if "system_id" not in esi_data:
            raise ValueError("system_id not found in moon response - data error")

        system_id = esi_data["system_id"]
        solar_system_data = EveSolarSystem.objects._fetch_from_esi(id=system_id)  # type: ignore
        if "planets" not in solar_system_data:
            raise ValueError("planets not found in solar system response - data error")

        for planet in solar_system_data["planets"]:
            if planet["planet_id"] == id:
                if "moons" in planet:
                    esi_data["moons"] = planet["moons"]

                if "asteroid_belts" in planet:
                    esi_data["asteroid_belts"] = planet["asteroid_belts"]

                return esi_data

        raise ValueError(
            f"Failed to find moon {id} in solar system response for {system_id} "
            f"- data error"
        )


class EvePlanetChildrenManager(EveUniverseEntityModelManager):
    """:meta private:"""

    def __init__(self) -> None:
        super().__init__()
        self._my_property_name = None

    def _fetch_from_esi(
        self,
        id: Optional[int] = None,
        _enabled_sections: Optional[Iterable[str]] = None,
    ) -> dict:
        from eveuniverse.models import EveSolarSystem

        if not self._my_property_name:
            raise RuntimeWarning("my_property_name not initialized")

        if id is None:
            raise ValueError("missing id")

        esi_data = super()._fetch_from_esi(id=id)
        if "system_id" not in esi_data:
            raise ValueError("system_id not found in moon response - data error")

        system_id = esi_data["system_id"]
        solar_system_data = EveSolarSystem.objects._fetch_from_esi(id=system_id)  # type: ignore
        if "planets" not in solar_system_data:
            raise ValueError("planets not found in solar system response - data error")

        for planet in solar_system_data["planets"]:
            if (
                self._my_property_name in planet
                and planet[self._my_property_name]
                and id in planet[self._my_property_name]
            ):
                esi_data["planet_id"] = planet["planet_id"]
                return esi_data

        raise ValueError(
            f"Failed to find moon {id} in solar system response for {system_id} "
            f"- data error"
        )


class EveAsteroidBeltManager(EvePlanetChildrenManager):
    """:meta private:"""

    def __init__(self) -> None:
        super().__init__()
        self._my_property_name = "asteroid_belts"


class EveMoonManager(EvePlanetChildrenManager):
    """:meta private:"""

    def __init__(self) -> None:
        super().__init__()
        self._my_property_name = "moons"


class EveStargateManager(EveUniverseEntityModelManager):
    """For special handling of relations

    :meta private:
    """

    def update_or_create_esi(
        self,
        *,
        id: int,
        include_children: bool = False,
        wait_for_children: bool = True,
        enabled_sections: Optional[Iterable[str]] = None,
        task_priority: Optional[int] = None,
    ) -> Tuple[Any, bool]:
        """updates or creates an EveStargate object by fetching it from ESI (blocking).
        Will always get/create parent objects

        Args:
            id: Eve Online ID of object
            include_children: (no effect)
            wait_for_children: (no effect)

        Returns:
            A tuple consisting of the requested object and a created flag
        """
        obj, created = super().update_or_create_esi(
            id=int(id),
            include_children=include_children,
            wait_for_children=wait_for_children,
            task_priority=task_priority,
        )
        if obj:
            if obj.destination_eve_stargate is not None:
                obj.destination_eve_stargate.destination_eve_stargate = obj

                if obj.eve_solar_system is not None:
                    obj.destination_eve_stargate.destination_eve_solar_system = (
                        obj.eve_solar_system
                    )
                obj.destination_eve_stargate.save()

        return obj, created


class EveTypeManager(EveUniverseEntityModelManager):
    """:meta private:"""

    def update_or_create_esi(
        self,
        *,
        id: int,
        include_children: bool = False,
        wait_for_children: bool = True,
        enabled_sections: Optional[Iterable[str]] = None,
        task_priority: Optional[int] = None,
    ) -> Tuple[Any, bool]:
        from eveuniverse.models import determine_effective_sections

        effective_sections = determine_effective_sections(enabled_sections)
        obj, created = super().update_or_create_esi(
            id=id,
            include_children=include_children,
            wait_for_children=wait_for_children,
            enabled_sections=effective_sections,
            task_priority=task_priority,
        )
        if effective_sections:
            if self.model.Section.TYPE_MATERIALS in effective_sections:
                from eveuniverse.models import EveTypeMaterial

                EveTypeMaterial.objects.update_or_create_api(eve_type=obj)  # type: ignore
            if self.model.Section.INDUSTRY_ACTIVITIES in effective_sections:
                from eveuniverse.models import (
                    EveIndustryActivityDuration,
                    EveIndustryActivityMaterial,
                    EveIndustryActivityProduct,
                    EveIndustryActivitySkill,
                )

                EveIndustryActivityDuration.objects.update_or_create_api(eve_type=obj)  # type: ignore
                EveIndustryActivityProduct.objects.update_or_create_api(eve_type=obj)  # type: ignore
                EveIndustryActivitySkill.objects.update_or_create_api(eve_type=obj)  # type: ignore
                EveIndustryActivityMaterial.objects.update_or_create_api(eve_type=obj)  # type: ignore
        return obj, created


class EveMarketPriceManager(models.Manager):
    """Custom manager for EveMarketPrice."""

    def update_from_esi(self, minutes_until_stale: Optional[int] = None) -> int:
        """Updates market prices from ESI. Will only create new price objects
        for EveTypes that already exist in the database.

        Args:
            minutes_until_stale: only prices older then given minutes are regarding
            as stale and will be updated. Will use default (60) if not specified.

        Returns:
            Count of updated types
        """
        from eveuniverse.models import EveType

        minutes_until_stale = (
            self.model.DEFAULT_MINUTES_UNTIL_STALE
            if minutes_until_stale is None
            else minutes_until_stale
        )

        logger.info("Fetching market prices from ESI...")
        entries = esi.client.Market.get_markets_prices().results()
        if not entries:
            return 0

        entries_2 = {int(x["type_id"]): x for x in entries if "type_id" in x}
        with transaction.atomic():
            existing_types_ids = set(EveType.objects.values_list("id", flat=True))
            relevant_prices_ids = set(entries_2.keys()).intersection(existing_types_ids)
            deadline = now() - dt.timedelta(minutes=minutes_until_stale)
            current_prices_ids = set(
                self.filter(updated_at__gt=deadline).values_list(
                    "eve_type_id", flat=True
                )
            )
            need_updating_ids = relevant_prices_ids.difference(current_prices_ids)
            if not need_updating_ids:
                logger.info("Market prices are up to date")
                return 0

            logger.info(
                "Updating market prices for %s types...", len(need_updating_ids)
            )
            self.filter(eve_type_id__in=need_updating_ids).delete()
            market_prices = [
                self.model(
                    eve_type=get_or_create_esi_or_none("type_id", entry, EveType),
                    adjusted_price=entry.get("adjusted_price"),
                    average_price=entry.get("average_price"),
                )
                for type_id, entry in entries_2.items()
                if type_id in need_updating_ids
            ]
            self.bulk_create(
                market_prices, batch_size=EVEUNIVERSE_BULK_METHODS_BATCH_SIZE
            )
            logger.info(
                "Completed updating market prices for %s types.", len(need_updating_ids)
            )
            return len(market_prices)
