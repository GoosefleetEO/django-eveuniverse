from enum import IntEnum


class EveCategoryId(IntEnum):
    SHIP = 6
    BLUEPRINT = 9
    STRUCTURE = 65
    SKIN = 91


class EveGroupId(IntEnum):
    CHARACTER = 1
    CORPORATION = 2
    SOLAR_SYSTEM = 5
    STAR = 6
    PLANET = 7
    MOON = 8
    ASTEROID_BELT = 9
    STARGATE = 10
    STATION = 15
    ALLIANCE = 32


# ESI
POST_UNIVERSE_NAMES_MAX_ITEMS = 1000
