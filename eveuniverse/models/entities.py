"""Entity models for Eve Universe."""

from typing import Set

from django.db import models

from eveuniverse.core import dotlan, eveimageserver, eveitems, evewho
from eveuniverse.managers import EveEntityManager

from .base import EveUniverseEntityModel


class EveEntity(EveUniverseEntityModel):
    """An Eve object from one of the categories supported by ESI's
    `/universe/names/` endpoint:

    alliance, character, constellation, faction, type, region, solar system, station


    This is a special model model dedicated to quick resolution of Eve IDs to names
    and their categories, e.g. for characters. See also manager methods.
    """

    # NPC IDs
    _NPC_CORPORATION_ID_BEGIN = 1_000_000
    _NPC_CORPORATION_ID_END = 2_000_000
    _NPC_CHARACTER_ID_BEGIN = 3_000_000
    _NPC_CHARACTER_ID_END = 4_000_000

    # categories
    CATEGORY_ALLIANCE = "alliance"
    CATEGORY_CHARACTER = "character"
    CATEGORY_CONSTELLATION = "constellation"
    CATEGORY_CORPORATION = "corporation"
    CATEGORY_FACTION = "faction"
    CATEGORY_INVENTORY_TYPE = "inventory_type"
    CATEGORY_REGION = "region"
    CATEGORY_SOLAR_SYSTEM = "solar_system"
    CATEGORY_STATION = "station"

    CATEGORY_CHOICES = (
        (CATEGORY_ALLIANCE, "alliance"),
        (CATEGORY_CHARACTER, "character"),
        (CATEGORY_CONSTELLATION, "constellation"),
        (CATEGORY_CORPORATION, "corporation"),
        (CATEGORY_FACTION, "faction"),
        (CATEGORY_INVENTORY_TYPE, "inventory_type"),
        (CATEGORY_REGION, "region"),
        (CATEGORY_SOLAR_SYSTEM, "solar_system"),
        (CATEGORY_STATION, "station"),
    )

    category = models.CharField(
        max_length=16, choices=CATEGORY_CHOICES, default=None, null=True
    )

    objects = EveEntityManager()

    class _EveUniverseMeta:
        esi_pk = "ids"
        esi_path_object = "Universe.post_universe_names"
        load_order = 110

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._categories = self.categories()

    def __str__(self) -> str:
        if self.name:
            return self.name
        return f"ID:{self.id}"

    @property
    def is_alliance(self) -> bool:
        """returns True if entity is an alliance, else False"""
        return self.is_category(self.CATEGORY_ALLIANCE)

    @property
    def is_character(self) -> bool:
        """returns True if entity is a character, else False"""
        return self.is_category(self.CATEGORY_CHARACTER)

    @property
    def is_constellation(self) -> bool:
        """returns True if entity is a constellation, else False"""
        return self.is_category(self.CATEGORY_CONSTELLATION)

    @property
    def is_corporation(self) -> bool:
        """returns True if entity is a corporation, else False"""
        return self.is_category(self.CATEGORY_CORPORATION)

    @property
    def is_faction(self) -> bool:
        """returns True if entity is a faction, else False"""
        return self.is_category(self.CATEGORY_FACTION)

    @property
    def is_type(self) -> bool:
        """returns True if entity is an inventory type, else False"""
        return self.is_category(self.CATEGORY_INVENTORY_TYPE)

    @property
    def is_region(self) -> bool:
        """returns True if entity is a region, else False"""
        return self.is_category(self.CATEGORY_REGION)

    @property
    def is_solar_system(self) -> bool:
        """returns True if entity is a solar system, else False"""
        return self.is_category(self.CATEGORY_SOLAR_SYSTEM)

    @property
    def is_station(self) -> bool:
        """returns True if entity is a station, else False"""
        return self.is_category(self.CATEGORY_STATION)

    @property
    def is_npc(self) -> bool:
        """True if this entity is an NPC character or NPC corporation, else False."""
        if (
            self.is_corporation
            and self._NPC_CORPORATION_ID_BEGIN <= self.id < self._NPC_CORPORATION_ID_END
        ):
            return True
        if (
            self.is_character
            and self._NPC_CHARACTER_ID_BEGIN <= self.id < self._NPC_CHARACTER_ID_END
        ):
            return True
        return False

    @property
    def is_npc_starter_corporation(self) -> bool:
        """True if this entity is an NPC starter corporation else False."""
        starter_corporation_ids = {
            1000165,  # Amarr - Hedion University
            1000166,  # Amarr - Imperial Academy
            1000077,  # Amarr - Royal Amarr Institute
            1000044,  # Caldari - School of Applied Knowledge
            1000045,  # Caldari - Science and Trade Institute
            1000167,  # Caldari - State War Academy
            1000169,  # Gallente - Center for Advanced Studies
            1000168,  # Gallente - Federal Navy Academy
            1000115,  # Gallente - University of Caille
            1000172,  # Minmatar - Pator Tech School
            1000170,  # Minmatar - Republic Military School
            1000171,  # Minmatar - Republic University
        }
        return self.is_corporation and self.id in starter_corporation_ids

    @property
    def profile_url(self) -> str:
        """URL to default third party website with profile info about this entity.

        Supported for:
        alliance, character, corporation, faction, region, solar system, station, type
        """
        if self.is_alliance:
            result = dotlan.alliance_url(self.name)

        elif self.is_character:
            result = evewho.character_url(self.id)

        elif self.is_corporation:
            result = dotlan.corporation_url(self.name)

        elif self.is_faction:
            result = dotlan.faction_url(self.name)

        elif self.is_region:
            result = dotlan.region_url(self.name)

        elif self.is_solar_system:
            result = dotlan.solar_system_url(self.name)

        elif self.is_station:
            result = dotlan.station_url(self.name)

        elif self.is_type:
            result = eveitems.type_url(self.id)

        else:
            result = ""

        return result

    def is_category(self, category: str) -> bool:
        """returns True if this entity has the given category, else False"""
        return category in self._categories and self.category == category

    def update_from_esi(self) -> "EveEntity":
        """Update the current object from ESI

        Returns:
            itself after update
        """
        obj = EveEntity.objects.update_or_create_esi(id=self.id)[0]  # type: ignore
        return obj

    def icon_url(self, size: int = EveUniverseEntityModel._DEFAULT_ICON_SIZE) -> str:
        """Create image URL for related EVE icon

        Args:
            size: size of image file in pixels, allowed values: 32, 64, 128, 256, 512

        Return:
            strings with image URL
        """
        map_category_2_other = {
            self.CATEGORY_ALLIANCE: "alliance_logo_url",
            self.CATEGORY_CHARACTER: "character_portrait_url",
            self.CATEGORY_CORPORATION: "corporation_logo_url",
            self.CATEGORY_FACTION: "faction_logo_url",
            self.CATEGORY_INVENTORY_TYPE: "type_icon_url",
        }
        if self.category not in map_category_2_other:
            return ""

        func = map_category_2_other[self.category]
        return getattr(eveimageserver, func)(self.id, size=size)

    @classmethod
    def categories(cls) -> Set[str]:
        """Set of valid categories."""
        return {x[0] for x in cls.CATEGORY_CHOICES}

    @classmethod
    def is_valid_category(cls, category: str) -> bool:
        """Wether given category is valid."""
        return category in cls.categories()
