"""Eve universe models."""

# pylint: disable = too-few-public-methods

import enum
import math
import re
from collections import namedtuple
from typing import Iterable, List, Optional, Set

from bitfield import BitField
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import models
from django.utils.functional import cached_property

from eveuniverse.app_settings import (
    EVEUNIVERSE_LOAD_ASTEROID_BELTS,
    EVEUNIVERSE_LOAD_DOGMAS,
    EVEUNIVERSE_LOAD_GRAPHICS,
    EVEUNIVERSE_LOAD_INDUSTRY_ACTIVITIES,
    EVEUNIVERSE_LOAD_MARKET_GROUPS,
    EVEUNIVERSE_LOAD_MOONS,
    EVEUNIVERSE_LOAD_PLANETS,
    EVEUNIVERSE_LOAD_STARGATES,
    EVEUNIVERSE_LOAD_STARS,
    EVEUNIVERSE_LOAD_STATIONS,
    EVEUNIVERSE_LOAD_TYPE_MATERIALS,
    EVEUNIVERSE_USE_EVESKINSERVER,
)
from eveuniverse.constants import EveCategoryId, EveGroupId, EveRegionId
from eveuniverse.core import dotlan, eveimageserver, eveitems, evesdeapi, eveskinserver
from eveuniverse.managers import (
    EveAsteroidBeltManager,
    EveMarketPriceManager,
    EveMoonManager,
    EvePlanetManager,
    EveStargateManager,
    EveTypeManager,
)
from eveuniverse.providers import esi

from .base import (
    NAMES_MAX_LENGTH,
    EveUniverseEntityModel,
    EveUniverseInlineModel,
    _SectionBase,
)
from .entities import EveEntity


def determine_effective_sections(
    enabled_sections: Optional[Iterable[str]] = None,
) -> Set[str]:
    """Determine currently effective sections."""
    enabled_sections = set(enabled_sections) if enabled_sections else set()
    if EVEUNIVERSE_LOAD_ASTEROID_BELTS:
        enabled_sections.add(EvePlanet.Section.ASTEROID_BELTS.value)
    if EVEUNIVERSE_LOAD_DOGMAS:
        enabled_sections.add(EveType.Section.DOGMAS.value)
    if EVEUNIVERSE_LOAD_GRAPHICS:
        enabled_sections.add(EveType.Section.GRAPHICS.value)
    if EVEUNIVERSE_LOAD_MARKET_GROUPS:
        enabled_sections.add(EveType.Section.MARKET_GROUPS.value)
    if EVEUNIVERSE_LOAD_MOONS:
        enabled_sections.add(EvePlanet.Section.MOONS.value)
    if EVEUNIVERSE_LOAD_PLANETS:
        enabled_sections.add(EveSolarSystem.Section.PLANETS.value)
    if EVEUNIVERSE_LOAD_STARGATES:
        enabled_sections.add(EveSolarSystem.Section.STARGATES.value)
    if EVEUNIVERSE_LOAD_STARS:
        enabled_sections.add(EveSolarSystem.Section.STARS.value)
    if EVEUNIVERSE_LOAD_STATIONS:
        enabled_sections.add(EveSolarSystem.Section.STATIONS.value)
    if EVEUNIVERSE_LOAD_TYPE_MATERIALS:
        enabled_sections.add(EveType.Section.TYPE_MATERIALS.value)
    if EVEUNIVERSE_LOAD_INDUSTRY_ACTIVITIES:
        enabled_sections.add(EveType.Section.INDUSTRY_ACTIVITIES.value)
    return enabled_sections


class EveAncestry(EveUniverseEntityModel):
    """An ancestry in Eve Online"""

    eve_bloodline = models.ForeignKey(
        "EveBloodline", on_delete=models.CASCADE, related_name="eve_bloodlines"
    )
    description = models.TextField()
    icon_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    short_description = models.TextField(default="")

    class _EveUniverseMeta:
        esi_pk = "id"
        esi_path_list = "Universe.get_universe_ancestries"
        esi_path_object = "Universe.get_universe_ancestries"
        field_mappings = {"eve_bloodline": "bloodline_id"}
        load_order = 180


class EveAsteroidBelt(EveUniverseEntityModel):
    """An asteroid belt in Eve Online"""

    eve_planet = models.ForeignKey(
        "EvePlanet", on_delete=models.CASCADE, related_name="eve_asteroid_belts"
    )
    position_x = models.FloatField(
        null=True, default=None, blank=True, help_text="x position in the solar system"
    )
    position_y = models.FloatField(
        null=True, default=None, blank=True, help_text="y position in the solar system"
    )
    position_z = models.FloatField(
        null=True, default=None, blank=True, help_text="z position in the solar system"
    )

    objects = EveAsteroidBeltManager()

    class _EveUniverseMeta:
        esi_pk = "asteroid_belt_id"
        esi_path_object = "Universe.get_universe_asteroid_belts_asteroid_belt_id"
        field_mappings = {
            "eve_planet": "planet_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        load_order = 200


class EveBloodline(EveUniverseEntityModel):
    """A bloodline in Eve Online"""

    eve_race = models.ForeignKey(
        "EveRace",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="eve_bloodlines",
    )
    eve_ship_type = models.ForeignKey(
        "EveType", on_delete=models.CASCADE, related_name="eve_bloodlines"
    )
    charisma = models.PositiveIntegerField()
    corporation_id = models.PositiveIntegerField()
    description = models.TextField()
    intelligence = models.PositiveIntegerField()
    memory = models.PositiveIntegerField()
    perception = models.PositiveIntegerField()
    willpower = models.PositiveIntegerField()

    class _EveUniverseMeta:
        esi_pk = "bloodline_id"
        esi_path_list = "Universe.get_universe_bloodlines"
        esi_path_object = "Universe.get_universe_bloodlines"
        field_mappings = {"eve_race": "race_id", "eve_ship_type": "ship_type_id"}
        load_order = 170


class EveCategory(EveUniverseEntityModel):
    """An inventory category in Eve Online"""

    published = models.BooleanField()

    class _EveUniverseMeta:
        esi_pk = "category_id"
        esi_path_list = "Universe.get_universe_categories"
        esi_path_object = "Universe.get_universe_categories_category_id"
        children = {"groups": "EveGroup"}
        load_order = 130


class EveConstellation(EveUniverseEntityModel):
    """A star constellation in Eve Online"""

    eve_region = models.ForeignKey(
        "EveRegion", on_delete=models.CASCADE, related_name="eve_constellations"
    )
    position_x = models.FloatField(
        null=True, default=None, blank=True, help_text="x position in the solar system"
    )
    position_y = models.FloatField(
        null=True, default=None, blank=True, help_text="y position in the solar system"
    )
    position_z = models.FloatField(
        null=True, default=None, blank=True, help_text="z position in the solar system"
    )

    class _EveUniverseMeta:
        esi_pk = "constellation_id"
        esi_path_list = "Universe.get_universe_constellations"
        esi_path_object = "Universe.get_universe_constellations_constellation_id"
        field_mappings = {
            "eve_region": "region_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        children = {"systems": "EveSolarSystem"}
        load_order = 192

    @classmethod
    def eve_entity_category(cls) -> str:
        return EveEntity.CATEGORY_CONSTELLATION


class EveDogmaAttribute(EveUniverseEntityModel):
    """A dogma attribute in Eve Online"""

    eve_unit = models.ForeignKey(
        "EveUnit",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="eve_units",
    )
    default_value = models.FloatField(default=None, null=True)
    description = models.TextField(default="")
    display_name = models.CharField(max_length=NAMES_MAX_LENGTH, default="")
    high_is_good = models.BooleanField(default=None, null=True)
    icon_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    published = models.BooleanField(default=None, null=True)
    stackable = models.BooleanField(default=None, null=True)

    class _EveUniverseMeta:
        esi_pk = "attribute_id"
        esi_path_list = "Dogma.get_dogma_attributes"
        esi_path_object = "Dogma.get_dogma_attributes_attribute_id"
        field_mappings = {"eve_unit": "unit_id"}
        load_order = 140


class EveDogmaEffect(EveUniverseEntityModel):
    """A dogma effect in Eve Online"""

    # we need to redefine the name field, because effect names can be very long
    name = models.CharField(
        max_length=400,
        default="",
        db_index=True,
        help_text="Eve Online name",
    )

    description = models.TextField(default="")
    disallow_auto_repeat = models.BooleanField(default=None, null=True)
    discharge_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="discharge_attribute_effects",
    )
    display_name = models.CharField(max_length=NAMES_MAX_LENGTH, default="")
    duration_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="duration_attribute_effects",
    )
    effect_category = models.PositiveIntegerField(default=None, null=True)
    electronic_chance = models.BooleanField(default=None, null=True)
    falloff_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="falloff_attribute_effects",
    )
    icon_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    is_assistance = models.BooleanField(default=None, null=True)
    is_offensive = models.BooleanField(default=None, null=True)
    is_warp_safe = models.BooleanField(default=None, null=True)
    post_expression = models.PositiveIntegerField(default=None, null=True)
    pre_expression = models.PositiveIntegerField(default=None, null=True)
    published = models.BooleanField(default=None, null=True)
    range_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="range_attribute_effects",
    )
    range_chance = models.BooleanField(default=None, null=True)
    tracking_speed_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="tracking_speed_attribute_effects",
    )

    class _EveUniverseMeta:
        esi_pk = "effect_id"
        esi_path_list = "Dogma.get_dogma_effects"
        esi_path_object = "Dogma.get_dogma_effects_effect_id"
        field_mappings = {
            "discharge_attribute": "discharge_attribute_id",
            "duration_attribute": "duration_attribute_id",
            "falloff_attribute": "falloff_attribute_id",
            "range_attribute": "range_attribute_id",
            "tracking_speed_attribute": "tracking_speed_attribute_id",
        }
        inline_objects = {
            "modifiers": "EveDogmaEffectModifier",
        }
        load_order = 142


class EveDogmaEffectModifier(EveUniverseInlineModel):
    """A modifier for a dogma effect in Eve Online"""

    domain = models.CharField(max_length=NAMES_MAX_LENGTH, default="")
    eve_dogma_effect = models.ForeignKey(
        "EveDogmaEffect", on_delete=models.CASCADE, related_name="modifiers"
    )
    func = models.CharField(max_length=NAMES_MAX_LENGTH)
    modified_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="modified_attribute_modifiers",
    )
    modifying_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="modifying_attribute_modifiers",
    )
    modifying_effect = models.ForeignKey(
        "EveDogmaEffect",
        on_delete=models.SET_DEFAULT,
        null=True,
        default=None,
        blank=True,
        related_name="modifying_effect_modifiers",
    )
    operator = models.IntegerField(default=None, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["eve_dogma_effect", "func"],
                name="fpk_evedogmaeffectmodifier",
            )
        ]

    class _EveUniverseMeta:
        parent_fk = "eve_dogma_effect"
        functional_pk = [
            "eve_dogma_effect",
            "func",
        ]
        field_mappings = {
            "modified_attribute": "modified_attribute_id",
            "modifying_attribute": "modifying_attribute_id",
            "modifying_effect": "effect_id",
        }
        load_order = 144


class EveUnit(EveUniverseEntityModel):
    """A unit in Eve Online"""

    display_name = models.CharField(max_length=50, default="")
    description = models.TextField(default="")

    objects = models.Manager()

    class _EveUniverseMeta:
        esi_pk = "unit_id"
        esi_path_object = None
        field_mappings = {
            "unit_id": "id",
            "unit_name": "name",
        }
        load_order = 100


class EveFaction(EveUniverseEntityModel):
    """A faction in Eve Online"""

    corporation_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    description = models.TextField()
    eve_solar_system = models.ForeignKey(
        "EveSolarSystem",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="eve_factions",
    )
    is_unique = models.BooleanField()
    militia_corporation_id = models.PositiveIntegerField(
        default=None, null=True, db_index=True
    )
    size_factor = models.FloatField()
    station_count = models.PositiveIntegerField()
    station_system_count = models.PositiveIntegerField()

    class _EveUniverseMeta:
        esi_pk = "faction_id"
        esi_path_list = "Universe.get_universe_factions"
        esi_path_object = "Universe.get_universe_factions"
        field_mappings = {"eve_solar_system": "solar_system_id"}
        load_order = 210

    @property
    def profile_url(self) -> str:
        """URL to default third party website with profile info about this entity."""
        return dotlan.faction_url(self.name)

    def logo_url(self, size=EveUniverseEntityModel.DEFAULT_ICON_SIZE) -> str:
        """returns an image URL for this faction

        Args:
            size: optional size of the image
        """
        return eveimageserver.faction_logo_url(self.id, size=size)

    @classmethod
    def eve_entity_category(cls) -> str:
        return EveEntity.CATEGORY_FACTION


class EveGraphic(EveUniverseEntityModel):
    """A graphic in Eve Online"""

    FILENAME_MAX_CHARS = 255

    collision_file = models.CharField(max_length=FILENAME_MAX_CHARS, default="")
    graphic_file = models.CharField(max_length=FILENAME_MAX_CHARS, default="")
    icon_folder = models.CharField(max_length=FILENAME_MAX_CHARS, default="")
    sof_dna = models.CharField(max_length=FILENAME_MAX_CHARS, default="")
    sof_fation_name = models.CharField(max_length=FILENAME_MAX_CHARS, default="")
    sof_hull_name = models.CharField(max_length=FILENAME_MAX_CHARS, default="")
    sof_race_name = models.CharField(max_length=FILENAME_MAX_CHARS, default="")

    class _EveUniverseMeta:
        esi_pk = "graphic_id"
        esi_path_list = "Universe.get_universe_graphics"
        esi_path_object = "Universe.get_universe_graphics_graphic_id"
        load_order = 120


class EveGroup(EveUniverseEntityModel):
    """An inventory group in Eve Online"""

    eve_category = models.ForeignKey(
        "EveCategory", on_delete=models.CASCADE, related_name="eve_groups"
    )
    published = models.BooleanField()

    class _EveUniverseMeta:
        esi_pk = "group_id"
        esi_path_list = "Universe.get_universe_groups"
        esi_path_object = "Universe.get_universe_groups_group_id"
        field_mappings = {"eve_category": "category_id"}
        children = {"types": "EveType"}
        load_order = 132


class EveMarketGroup(EveUniverseEntityModel):
    """A market group in Eve Online"""

    description = models.TextField()
    parent_market_group = models.ForeignKey(
        "self",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="market_group_children",
    )

    class _EveUniverseMeta:
        esi_pk = "market_group_id"
        esi_path_list = "Market.get_markets_groups"
        esi_path_object = "Market.get_markets_groups_market_group_id"
        field_mappings = {"parent_market_group": "parent_group_id"}
        children = {"types": "EveType"}
        load_order = 230


class EveMarketPrice(models.Model):
    """A market price of an Eve Online type"""

    DEFAULT_MINUTES_UNTIL_STALE = 60

    eve_type = models.OneToOneField(
        "EveType",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="market_price",
    )
    adjusted_price = models.FloatField(default=None, null=True)
    average_price = models.FloatField(default=None, null=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    objects = EveMarketPriceManager()

    def __str__(self) -> str:
        return f"{self.eve_type}: {self.average_price}"

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(eve_type='{self.eve_type}', "
            f"adjusted_price={self.adjusted_price}, average_price={self.average_price}, "
            f"updated_at={self.updated_at})"
        )


class EveMoon(EveUniverseEntityModel):
    """A moon in Eve Online"""

    eve_planet = models.ForeignKey(
        "EvePlanet", on_delete=models.CASCADE, related_name="eve_moons"
    )
    position_x = models.FloatField(
        null=True, default=None, blank=True, help_text="x position in the solar system"
    )
    position_y = models.FloatField(
        null=True, default=None, blank=True, help_text="y position in the solar system"
    )
    position_z = models.FloatField(
        null=True, default=None, blank=True, help_text="z position in the solar system"
    )

    objects = EveMoonManager()

    class _EveUniverseMeta:
        esi_pk = "moon_id"
        esi_path_object = "Universe.get_universe_moons_moon_id"
        field_mappings = {
            "eve_planet": "planet_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        load_order = 220


class EvePlanet(EveUniverseEntityModel):
    """A planet in Eve Online"""

    class Section(_SectionBase):
        """Sections that can be optionally loaded with each instance"""

        ASTEROID_BELTS = "asteroid_belts"  #:
        MOONS = "moons"  #:

    eve_solar_system = models.ForeignKey(
        "EveSolarSystem", on_delete=models.CASCADE, related_name="eve_planets"
    )
    eve_type = models.ForeignKey(
        "EveType", on_delete=models.CASCADE, related_name="eve_planets"
    )
    position_x = models.FloatField(
        null=True, default=None, blank=True, help_text="x position in the solar system"
    )
    position_y = models.FloatField(
        null=True, default=None, blank=True, help_text="y position in the solar system"
    )
    position_z = models.FloatField(
        null=True, default=None, blank=True, help_text="z position in the solar system"
    )
    enabled_sections = BitField(
        flags=tuple(Section.values()),
        help_text=(
            "Flags for loadable sections. True if instance was loaded with section."
        ),  # no index, because MySQL does not support it for bitwise operations
    )  # type: ignore

    objects = EvePlanetManager()

    class _EveUniverseMeta:
        esi_pk = "planet_id"
        esi_path_object = "Universe.get_universe_planets_planet_id"
        field_mappings = {
            "eve_solar_system": "system_id",
            "eve_type": "type_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        children = {"moons": "EveMoon", "asteroid_belts": "EveAsteroidBelt"}
        load_order = 205

    def type_name(self) -> str:
        """Return shortened name of planet type.

        Note: Accesses the eve_type object.
        """
        matches = re.findall(r"Planet \((\S*)\)", self.eve_type.name)
        return matches[0] if matches else ""

    @classmethod
    def _children(cls, enabled_sections: Optional[Iterable[str]] = None) -> dict:
        enabled_sections = determine_effective_sections(enabled_sections)
        children = {}
        if cls.Section.ASTEROID_BELTS in enabled_sections:
            children["asteroid_belts"] = "EveAsteroidBelt"
        if cls.Section.MOONS in enabled_sections:
            children["moons"] = "EveMoon"
        return children


class EveRace(EveUniverseEntityModel):
    """A race in Eve Online"""

    alliance_id = models.PositiveIntegerField(db_index=True)
    description = models.TextField()

    class _EveUniverseMeta:
        esi_pk = "race_id"
        esi_path_list = "Universe.get_universe_races"
        esi_path_object = "Universe.get_universe_races"
        load_order = 150


class EveRegion(EveUniverseEntityModel):
    """A star region in Eve Online"""

    description = models.TextField(default="")

    class _EveUniverseMeta:
        esi_pk = "region_id"
        esi_path_list = "Universe.get_universe_regions"
        esi_path_object = "Universe.get_universe_regions_region_id"
        children = {"constellations": "EveConstellation"}
        load_order = 190

    @property
    def profile_url(self) -> str:
        """URL to default third party website with profile info about this entity."""
        return dotlan.region_url(self.name)

    @classmethod
    def eve_entity_category(cls) -> str:
        return EveEntity.CATEGORY_REGION


class EveSolarSystem(EveUniverseEntityModel):
    """A solar system in Eve Online"""

    class Section(_SectionBase):
        """Sections that can be optionally loaded with each instance"""

        PLANETS = "planets"  #:
        STARGATES = "stargates"  #:
        STARS = "stars"  #:
        STATIONS = "stations"  #:

    eve_constellation = models.ForeignKey(
        "EveConstellation", on_delete=models.CASCADE, related_name="eve_solarsystems"
    )
    eve_star = models.OneToOneField(
        "EveStar",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="eve_solarsystem",
    )
    position_x = models.FloatField(
        null=True, default=None, blank=True, help_text="x position in the solar system"
    )
    position_y = models.FloatField(
        null=True, default=None, blank=True, help_text="y position in the solar system"
    )
    position_z = models.FloatField(
        null=True, default=None, blank=True, help_text="z position in the solar system"
    )
    security_status = models.FloatField()
    enabled_sections = BitField(
        flags=tuple(Section.values()),
        help_text=(
            "Flags for loadable sections. True if instance was loaded with section."
        ),  # no index, because MySQL does not support it for bitwise operations
    )  # type: ignore

    class _EveUniverseMeta:
        esi_pk = "system_id"
        esi_path_list = "Universe.get_universe_systems"
        esi_path_object = "Universe.get_universe_systems_system_id"
        field_mappings = {
            "eve_constellation": "constellation_id",
            "eve_star": "star_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        children = {}
        load_order = 194

    NearestCelestial = namedtuple(
        "NearestCelestial", ["eve_type", "eve_object", "distance"]
    )
    NearestCelestial.__doc__ = "Container for a nearest celestial"

    @property
    def profile_url(self) -> str:
        """URL to default third party website with profile info about this entity."""
        return dotlan.solar_system_url(self.name)

    @property
    def is_high_sec(self) -> bool:
        """returns True if this solar system is in high sec, else False"""
        return round(self.security_status, 1) >= 0.5

    @property
    def is_low_sec(self) -> bool:
        """returns True if this solar system is in low sec, else False"""
        return 0 < round(self.security_status, 1) < 0.5

    @property
    def is_null_sec(self) -> bool:
        """returns True if this solar system is in null sec, else False"""
        return (
            not self.is_w_space
            and not self.is_trig_space
            and round(self.security_status, 1) <= 0
            and not self.is_w_space
        )

    @property
    def is_w_space(self) -> bool:
        """returns True if this solar system is in wormhole space, else False"""
        return 31000000 <= self.id < 32000000

    @cached_property
    def is_trig_space(self) -> bool:
        """returns True if this solar system is in Triglavian space, else False"""
        return self.eve_constellation.eve_region_id == EveRegionId.POCHVEN

    @classmethod
    def eve_entity_category(cls) -> str:
        return EveEntity.CATEGORY_SOLAR_SYSTEM

    def distance_to(self, destination: "EveSolarSystem") -> Optional[float]:
        """Calculates the distance in meters between the current and the given solar system

        Args:
            destination: Other solar system to use in calculation

        Returns:
            Distance in meters or None if one of the systems is in WH space
        """
        if not self.position_x or not self.position_y or not self.position_z:
            return None
        if (
            not destination
            or not destination.position_x
            or not destination.position_y
            or not destination.position_z
        ):
            return None

        if (
            self.is_w_space
            or destination.is_w_space
            or self.is_trig_space
            or destination.is_trig_space
        ):
            return None

        return math.sqrt(
            (destination.position_x - self.position_x) ** 2
            + (destination.position_y - self.position_y) ** 2
            + (destination.position_z - self.position_z) ** 2
        )

    def route_to(
        self, destination: "EveSolarSystem"
    ) -> Optional[List["EveSolarSystem"]]:
        """Calculates the shortest route between the current and the given solar system

        Args:
            destination: Other solar system to use in calculation

        Returns:
            List of solar system objects incl. origin and destination
            or None if no route can be found (e.g. if one system is in WH space)
        """
        if (
            self.is_w_space
            or destination.is_w_space
            or self.is_trig_space
            or destination.is_trig_space
        ):
            return None

        path_ids = self._calc_route_esi(self.id, destination.id)
        if path_ids is None:
            return None

        return [
            EveSolarSystem.objects.get_or_create_esi(id=solar_system_id)
            for solar_system_id in path_ids
        ]

    def jumps_to(self, destination: "EveSolarSystem") -> Optional[int]:
        """Calculates the shortest route between the current and the given solar system

        Args:
            destination: Other solar system to use in calculation

        Returns:
            Number of total jumps
            or None if no route can be found (e.g. if one system is in WH space)
        """
        if (
            self.is_w_space
            or destination.is_w_space
            or self.is_trig_space
            or destination.is_trig_space
        ):
            return None

        path_ids = self._calc_route_esi(self.id, destination.id)
        return len(path_ids) - 1 if path_ids is not None else None

    @staticmethod
    def _calc_route_esi(origin_id: int, destination_id: int) -> Optional[List[int]]:
        """returns the shortest route between two given solar systems.

        Route is calculated by ESI

        Args:
            destination_id: ID of the other solar system to use in calculation

        Returns:
            List of solar system IDs incl. origin and destination
            or None if no route can be found (e.g. if one system is in WH space)
        """

        try:
            return esi.client.Routes.get_route_origin_destination(
                origin=origin_id, destination=destination_id
            ).results()
        except OSError:  # FIXME: ESI is supposed to return 404,
            # but django-esi is actually returning an OSError
            return None

    def nearest_celestial(
        self, x: int, y: int, z: int, group_id: Optional[int] = None
    ) -> Optional[NearestCelestial]:
        """Determine nearest celestial to given coordinates as eveuniverse object.

        Args:
            x, y, z: Start point in space to look from
            group_id: Eve ID of group to filter results by

        Raises:
            HTTPError: If an HTTP error is encountered

        Returns:
            Eve item or None if none is found
        """
        item = evesdeapi.nearest_celestial(
            solar_system_id=self.id, x=x, y=y, z=z, group_id=group_id
        )
        if not item:
            return None
        eve_type, _ = EveType.objects.get_or_create_esi(id=item.type_id)
        class_mapping = {
            EveGroupId.ASTEROID_BELT: EveAsteroidBelt,
            EveGroupId.MOON: EveMoon,
            EveGroupId.PLANET: EvePlanet,
            EveGroupId.STAR: EveStar,
            EveGroupId.STARGATE: EveStargate,
            EveGroupId.STATION: EveStation,
        }
        try:
            my_class = class_mapping[eve_type.eve_group_id]
        except KeyError:
            return None
        obj, _ = my_class.objects.get_or_create_esi(id=item.id)
        return self.NearestCelestial(
            eve_type=eve_type, eve_object=obj, distance=item.distance
        )

    @classmethod
    def _children(cls, enabled_sections: Optional[Iterable[str]] = None) -> dict:
        enabled_sections = determine_effective_sections(enabled_sections)
        children = {}
        if cls.Section.PLANETS in enabled_sections:
            children["planets"] = "EvePlanet"
        if cls.Section.STARGATES in enabled_sections:
            children["stargates"] = "EveStargate"
        if cls.Section.STATIONS in enabled_sections:
            children["stations"] = "EveStation"
        return children

    @classmethod
    def _disabled_fields(cls, enabled_sections: Optional[Set[str]] = None) -> set:
        enabled_sections = determine_effective_sections(enabled_sections)
        if cls.Section.STARS not in enabled_sections:
            return {"eve_star"}
        return set()

    @classmethod
    def _inline_objects(cls, enabled_sections: Optional[Set[str]] = None) -> dict:
        if not enabled_sections or cls.Section.PLANETS not in enabled_sections:
            return {}
        return super()._inline_objects()


class EveStar(EveUniverseEntityModel):
    """A star in Eve Online"""

    age = models.BigIntegerField()
    eve_type = models.ForeignKey(
        "EveType", on_delete=models.CASCADE, related_name="eve_stars"
    )
    luminosity = models.FloatField()
    radius = models.PositiveIntegerField()
    spectral_class = models.CharField(max_length=16)
    temperature = models.PositiveIntegerField()

    class _EveUniverseMeta:
        esi_pk = "star_id"
        esi_path_object = "Universe.get_universe_stars_star_id"
        field_mappings = {"eve_type": "type_id"}
        load_order = 222


class EveStargate(EveUniverseEntityModel):
    """A stargate in Eve Online"""

    destination_eve_stargate = models.OneToOneField(
        "EveStargate", on_delete=models.SET_DEFAULT, null=True, default=None, blank=True
    )
    destination_eve_solar_system = models.ForeignKey(
        "EveSolarSystem",
        on_delete=models.SET_DEFAULT,
        null=True,
        default=None,
        blank=True,
        related_name="destination_eve_stargates",
    )
    eve_solar_system = models.ForeignKey(
        "EveSolarSystem", on_delete=models.CASCADE, related_name="eve_stargates"
    )
    eve_type = models.ForeignKey(
        "EveType", on_delete=models.CASCADE, related_name="eve_stargates"
    )
    position_x = models.FloatField(
        null=True, default=None, blank=True, help_text="x position in the solar system"
    )
    position_y = models.FloatField(
        null=True, default=None, blank=True, help_text="y position in the solar system"
    )
    position_z = models.FloatField(
        null=True, default=None, blank=True, help_text="z position in the solar system"
    )

    objects = EveStargateManager()

    class _EveUniverseMeta:
        esi_pk = "stargate_id"
        esi_path_object = "Universe.get_universe_stargates_stargate_id"
        field_mappings = {
            "destination_eve_stargate": ("destination", "stargate_id"),
            "destination_eve_solar_system": ("destination", "system_id"),
            "eve_solar_system": "system_id",
            "eve_type": "type_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        dont_create_related = {
            "destination_eve_stargate",
            "destination_eve_solar_system",
        }
        load_order = 224


class EveStation(EveUniverseEntityModel):
    """A space station in Eve Online"""

    eve_race = models.ForeignKey(
        "EveRace",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="eve_stations",
    )
    eve_solar_system = models.ForeignKey(
        "EveSolarSystem",
        on_delete=models.CASCADE,
        related_name="eve_stations",
    )
    eve_type = models.ForeignKey(
        "EveType",
        on_delete=models.CASCADE,
        related_name="eve_stations",
    )
    max_dockable_ship_volume = models.FloatField()
    office_rental_cost = models.FloatField()
    owner_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    position_x = models.FloatField(
        null=True, default=None, blank=True, help_text="x position in the solar system"
    )
    position_y = models.FloatField(
        null=True, default=None, blank=True, help_text="y position in the solar system"
    )
    position_z = models.FloatField(
        null=True, default=None, blank=True, help_text="z position in the solar system"
    )
    reprocessing_efficiency = models.FloatField()
    reprocessing_stations_take = models.FloatField()
    services = models.ManyToManyField("EveStationService")

    class _EveUniverseMeta:
        esi_pk = "station_id"
        esi_path_object = "Universe.get_universe_stations_station_id"
        field_mappings = {
            "eve_race": "race_id",
            "eve_solar_system": "system_id",
            "eve_type": "type_id",
            "owner_id": "owner",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        inline_objects = {"services": "EveStationService"}
        load_order = 207

    @classmethod
    def eve_entity_category(cls) -> str:
        return EveEntity.CATEGORY_STATION

    @classmethod
    def update_or_create_inline_objects(
        self,
        *,
        parent_eve_data_obj: dict,
        parent_obj,
        inline_objects: dict,
        wait_for_children: bool,
        enabled_sections: Iterable[str],
        task_priority: Optional[int] = None,
    ) -> None:
        """updates_or_creates station service objects for EveStations"""

        if "services" in parent_eve_data_obj:
            services = []
            for service_name in parent_eve_data_obj["services"]:
                service, _ = EveStationService.objects.get_or_create(name=service_name)
                services.append(service)

            if services:
                parent_obj.services.add(*services)


class EveStationService(models.Model):
    """A service in a space station"""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class EveType(EveUniverseEntityModel):
    """An inventory type in Eve Online"""

    class Section(_SectionBase):
        """Sections that can be optionally loaded with each instance"""

        DOGMAS = "dogmas"  #:
        GRAPHICS = "graphics"  #:
        MARKET_GROUPS = "market_groups"  #:
        TYPE_MATERIALS = "type_materials"  #:
        INDUSTRY_ACTIVITIES = "industry_activities"  #:

    capacity = models.FloatField(default=None, null=True)
    description = models.TextField(default="")
    eve_group = models.ForeignKey(
        "EveGroup",
        on_delete=models.CASCADE,
        related_name="eve_types",
    )
    eve_graphic = models.ForeignKey(
        "EveGraphic",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="eve_types",
    )
    icon_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    eve_market_group = models.ForeignKey(
        "EveMarketGroup",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="eve_types",
    )
    mass = models.FloatField(default=None, null=True)
    packaged_volume = models.FloatField(default=None, null=True)
    portion_size = models.PositiveIntegerField(default=None, null=True)
    radius = models.FloatField(default=None, null=True)
    published = models.BooleanField()
    volume = models.FloatField(default=None, null=True)
    enabled_sections = BitField(
        flags=tuple(Section.values()),
        help_text=(
            "Flags for loadable sections. True if instance was loaded with section."
        ),  # no index, because MySQL does not support it for bitwise operations
    )  # type: ignore

    objects = EveTypeManager()

    class _EveUniverseMeta:
        esi_pk = "type_id"
        esi_path_list = "Universe.get_universe_types"
        esi_path_object = "Universe.get_universe_types_type_id"
        field_mappings = {
            "eve_graphic": "graphic_id",
            "eve_group": "group_id",
            "eve_market_group": "market_group_id",
        }
        inline_objects = {
            "dogma_attributes": "EveTypeDogmaAttribute",
            "dogma_effects": "EveTypeDogmaEffect",
        }
        load_order = 134

    @property
    def profile_url(self) -> str:
        """URL to display this type on the default third party webpage."""
        return eveitems.type_url(self.id)

    class IconVariant(enum.Enum):
        """Variant of icon to produce with `icon_url()`"""

        REGULAR = enum.auto()
        """anything, except blueprint or skin"""

        BPO = enum.auto()
        """blueprint original"""

        BPC = enum.auto()
        """blueprint copy"""

        SKIN = enum.auto()
        """SKIN"""

    def icon_url(
        self,
        size: int = EveUniverseEntityModel.DEFAULT_ICON_SIZE,
        variant: Optional[IconVariant] = None,
        category_id: Optional[int] = None,
        is_blueprint: Optional[bool] = None,
    ) -> str:
        """returns an image URL to this type as icon. Also works for blueprints and SKINs.

        Will try to auto-detect the variant based on the types's category,
        unless `variant` or `category_id` is specified.

        Args:
            variant: icon variant to use
            category_id: category ID of this type
            is_blueprint: DEPRECATED - type is assumed to be a blueprint
        """
        # if is_blueprint is not None:
        #    warnings.warn("is_blueprint in EveType.icon_url() is deprecated")

        if is_blueprint:
            variant = self.IconVariant.BPO

        if not variant:
            if not category_id:
                category_id = self.eve_group.eve_category_id

            if category_id == EveCategoryId.BLUEPRINT:
                variant = self.IconVariant.BPO

            elif category_id == EveCategoryId.SKIN:
                variant = self.IconVariant.SKIN

        if variant is self.IconVariant.BPO:
            return eveimageserver.type_bp_url(self.id, size=size)

        if variant is self.IconVariant.BPC:
            return eveimageserver.type_bpc_url(self.id, size=size)

        if variant is self.IconVariant.SKIN:
            size = EveUniverseEntityModel.DEFAULT_ICON_SIZE if not size else size
            if EVEUNIVERSE_USE_EVESKINSERVER:
                return eveskinserver.type_icon_url(self.id, size=size)

            if size < 32 or size > 128 or (size & (size - 1) != 0):
                raise ValueError(f"Invalid size: {size}")

            filename = f"eveuniverse/skin_generic_{size}.png"
            return staticfiles_storage.url(filename)

        return eveimageserver.type_icon_url(self.id, size=size)

    def render_url(self, size=EveUniverseEntityModel.DEFAULT_ICON_SIZE) -> str:
        """return an image URL to this type as render"""
        return eveimageserver.type_render_url(self.id, size=size)

    @classmethod
    def _disabled_fields(cls, enabled_sections: Optional[Set[str]] = None) -> set:
        enabled_sections = determine_effective_sections(enabled_sections)
        disabled_fields = set()
        if cls.Section.GRAPHICS not in enabled_sections:
            disabled_fields.add("eve_graphic")
        if cls.Section.MARKET_GROUPS not in enabled_sections:
            disabled_fields.add("eve_market_group")
        return disabled_fields

    @classmethod
    def _inline_objects(cls, enabled_sections: Optional[Set[str]] = None) -> dict:
        if not enabled_sections or cls.Section.DOGMAS not in enabled_sections:
            return {}
        return super()._inline_objects()

    @classmethod
    def eve_entity_category(cls) -> str:
        return EveEntity.CATEGORY_INVENTORY_TYPE


class EveTypeDogmaAttribute(EveUniverseInlineModel):
    """A dogma attribute of on inventory type in Eve Online"""

    eve_dogma_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.CASCADE,
        related_name="eve_type_dogma_attributes",
    )
    eve_type = models.ForeignKey(
        "EveType", on_delete=models.CASCADE, related_name="dogma_attributes"
    )
    value = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["eve_type", "eve_dogma_attribute"],
                name="fpk_evetypedogmaattribute",
            )
        ]

    class _EveUniverseMeta:
        parent_fk = "eve_type"
        functional_pk = [
            "eve_type",
            "eve_dogma_attribute",
        ]
        field_mappings = {"eve_dogma_attribute": "attribute_id"}
        load_order = 148


class EveTypeDogmaEffect(EveUniverseInlineModel):
    """A dogma effect of on inventory type in Eve Online"""

    eve_dogma_effect = models.ForeignKey(
        "EveDogmaEffect",
        on_delete=models.CASCADE,
        related_name="eve_type_dogma_effects",
    )
    eve_type = models.ForeignKey(
        "EveType", on_delete=models.CASCADE, related_name="dogma_effects"
    )
    is_default = models.BooleanField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["eve_type", "eve_dogma_effect"],
                name="fpk_evetypedogmaeffect",
            )
        ]

    class _EveUniverseMeta:
        parent_fk = "eve_type"
        functional_pk = [
            "eve_type",
            "eve_dogma_effect",
        ]
        field_mappings = {"eve_dogma_effect": "effect_id"}
        load_order = 146
