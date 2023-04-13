from unittest.mock import patch

from eveuniverse.models import EveType, EveUniverseEntityModel
from eveuniverse.utils import NoSocketsTestCase

MODELS_PATH = "eveuniverse.models"


class TestDetermineEnabledSections(NoSocketsTestCase):
    def test_should_return_empty_1(self):
        # when
        with patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", False), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False
        ), patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False
        ):
            result = EveUniverseEntityModel.determine_effective_sections()
        # then
        self.assertSetEqual(result, set())

    def test_should_return_empty_2(self):
        # when
        with patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", False), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False
        ), patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False
        ):
            result = EveUniverseEntityModel.determine_effective_sections(None)
        # then
        self.assertSetEqual(result, set())

    def test_should_return_global_section(self):
        # when
        with patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", False), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True
        ), patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False
        ):
            result = EveUniverseEntityModel.determine_effective_sections()
        # then
        self.assertSetEqual(result, {EveType.Section.DOGMAS})

    def test_should_combine_global_and_local_sections(self):
        # when
        with patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", False), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True
        ), patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False
        ), patch(
            MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False
        ):
            result = EveUniverseEntityModel.determine_effective_sections(
                ["type_materials"]
            )
        # then
        self.assertSetEqual(
            result, {EveType.Section.DOGMAS, EveType.Section.TYPE_MATERIALS}
        )
