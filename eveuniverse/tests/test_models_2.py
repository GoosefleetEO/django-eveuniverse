import unittest
from unittest.mock import patch

from django.test.utils import override_settings

from ..constants import EveCategoryId
from ..models import (
    EsiMapping,
    EveAncestry,
    EveBloodline,
    EveCategory,
    EveConstellation,
    EveDogmaAttribute,
    EveDogmaEffect,
    EveEntity,
    EveGraphic,
    EveGroup,
    EveMarketGroup,
    EveRegion,
    EveType,
    EveTypeDogmaEffect,
    EveUnit,
)
from ..utils import NoSocketsTestCase
from .testdata.esi import BravadoOperationStub, EsiClientStub
from .testdata.factories import create_eve_entity

unittest.util._MAX_LENGTH = 1000
MODELS_PATH = "eveuniverse.models"
MANAGERS_PATH = "eveuniverse.managers"


@patch(MANAGERS_PATH + ".esi")
class TestEveType(NoSocketsTestCase):
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    def test_can_create_type_from_esi_excluding_all(self, mock_esi):
        mock_esi.client = EsiClientStub()

        obj, created = EveType.objects.get_or_create_esi(id=603)
        self.assertTrue(created)
        self.assertEqual(obj.id, 603)
        self.assertEqual(obj.name, "Merlin")
        self.assertEqual(
            obj.description,
            """The Merlin is the most powerful combat frigate of the Caldari. Its role has evolved through the years, and while its defenses have always remained exceptionally strong for a Caldari vessel, its offensive capabilities have evolved from versatile, jack-of-all-trades attack patterns into focused and deadly gunfire tactics. The Merlin's primary aim is to have its turrets punch holes in opponents' hulls.""",
        )
        self.assertEqual(obj.capacity, 150)
        self.assertEqual(obj.eve_group, EveGroup.objects.get(id=25))
        self.assertEqual(obj.mass, 997000)
        self.assertEqual(obj.packaged_volume, 2500)
        self.assertEqual(obj.portion_size, 1)
        self.assertTrue(obj.published)
        self.assertEqual(obj.radius, 39)
        self.assertEqual(obj.volume, 16500)
        self.assertIsNone(obj.eve_graphic)
        self.assertIsNone(obj.eve_market_group)
        self.assertEqual(obj.dogma_attributes.count(), 0)
        self.assertEqual(obj.dogma_effects.count(), 0)
        self.assertEqual(obj.eve_entity_category(), EveEntity.CATEGORY_INVENTORY_TYPE)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", True)
    def test_can_create_type_from_esi_including_dogmas(self, mock_esi):
        mock_esi.client = EsiClientStub()

        eve_type, created = EveType.objects.get_or_create_esi(id=603)
        self.assertTrue(created)
        self.assertEqual(eve_type.id, 603)
        self.assertEqual(eve_type.eve_graphic, EveGraphic.objects.get(id=314))
        self.assertEqual(eve_type.eve_market_group, EveMarketGroup.objects.get(id=61))

        dogma_attribute_1 = eve_type.dogma_attributes.filter(
            eve_dogma_attribute=EveDogmaAttribute.objects.get(id=588)
        ).first()
        self.assertEqual(dogma_attribute_1.value, 5)
        dogma_attribute_1 = eve_type.dogma_attributes.filter(
            eve_dogma_attribute=EveDogmaAttribute.objects.get(id=129)
        ).first()
        self.assertEqual(dogma_attribute_1.value, 12)

        dogma_effect_1 = eve_type.dogma_effects.filter(
            eve_dogma_effect=EveDogmaEffect.objects.get(id=1816)
        ).first()
        self.assertFalse(dogma_effect_1.is_default)
        dogma_effect_2 = eve_type.dogma_effects.filter(
            eve_dogma_effect=EveDogmaEffect.objects.get(id=1817)
        ).first()
        self.assertTrue(dogma_effect_2.is_default)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    def test_when_disabled_can_create_type_from_esi_excluding_dogmas(self, mock_esi):
        mock_esi.client = EsiClientStub()

        obj, created = EveType.objects.get_or_create_esi(id=603)
        self.assertTrue(created)
        self.assertEqual(obj.id, 603)
        self.assertTrue(obj.eve_market_group, EveMarketGroup.objects.get(id=61))
        self.assertEqual(obj.dogma_attributes.count(), 0)
        self.assertEqual(obj.dogma_effects.count(), 0)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
    def test_when_disabled_can_create_type_from_esi_excluding_market_groups(
        self, mock_esi
    ):
        mock_esi.client = EsiClientStub()

        eve_type, created = EveType.objects.get_or_create_esi(id=603)
        self.assertTrue(created)
        self.assertEqual(eve_type.id, 603)
        self.assertIsNone(eve_type.eve_market_group)
        self.assertSetEqual(
            set(
                eve_type.dogma_attributes.values_list(
                    "eve_dogma_attribute_id", flat=True
                )
            ),
            {588, 129},
        )
        self.assertSetEqual(
            set(eve_type.dogma_effects.values_list("eve_dogma_effect_id", flat=True)),
            {1816, 1817},
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    def test_can_create_type_from_esi_including_dogmas_when_disabled_1(self, mock_esi):
        mock_esi.client = EsiClientStub()

        eve_type, created = EveType.objects.update_or_create_esi(
            id=603, enabled_sections=[EveType.LOAD_DOGMAS]
        )
        self.assertTrue(created)
        self.assertEqual(eve_type.id, 603)
        self.assertSetEqual(
            set(
                eve_type.dogma_attributes.values_list(
                    "eve_dogma_attribute_id", flat=True
                )
            ),
            {588, 129},
        )
        self.assertSetEqual(
            set(eve_type.dogma_effects.values_list("eve_dogma_effect_id", flat=True)),
            {1816, 1817},
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    def test_can_create_type_from_esi_including_dogmas_when_disabled_2(self, mock_esi):
        mock_esi.client = EsiClientStub()

        eve_type, created = EveType.objects.get_or_create_esi(
            id=603, enabled_sections=[EveType.LOAD_DOGMAS]
        )
        self.assertTrue(created)
        self.assertEqual(eve_type.id, 603)
        self.assertSetEqual(
            set(
                eve_type.dogma_attributes.values_list(
                    "eve_dogma_attribute_id", flat=True
                )
            ),
            {588, 129},
        )
        self.assertSetEqual(
            set(eve_type.dogma_effects.values_list("eve_dogma_effect_id", flat=True)),
            {1816, 1817},
        )

    @override_settings(
        CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True
    )
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    def test_can_create_type_from_esi_including_children_as_task(self, mock_esi):
        mock_esi.client = EsiClientStub()

        eve_type, created = EveType.objects.update_or_create_esi(
            id=603, wait_for_children=False, enabled_sections=[EveType.LOAD_DOGMAS]
        )
        self.assertTrue(created)
        self.assertEqual(eve_type.id, 603)
        self.assertSetEqual(
            set(
                eve_type.dogma_attributes.values_list(
                    "eve_dogma_attribute_id", flat=True
                )
            ),
            {588, 129},
        )
        self.assertSetEqual(
            set(eve_type.dogma_effects.values_list("eve_dogma_effect_id", flat=True)),
            {1816, 1817},
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    def test_can_create_render_url(self, mock_esi):
        mock_esi.client = EsiClientStub()

        eve_type, created = EveType.objects.get_or_create_esi(id=603)
        self.assertTrue(created)
        self.assertEqual(
            eve_type.render_url(256),
            "https://images.evetech.net/types/603/render?size=256",
        )


@patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
@patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
@patch(MANAGERS_PATH + ".esi")
class TestEveTypeIconUrl(NoSocketsTestCase):
    def test_can_create_icon_url_1(self, mock_esi):
        """icon from regular type, automatically detected"""
        mock_esi.client = EsiClientStub()
        eve_type, _ = EveType.objects.get_or_create_esi(id=603)

        self.assertEqual(
            eve_type.icon_url(256), "https://images.evetech.net/types/603/icon?size=256"
        )

    def test_can_create_icon_url_2(self, mock_esi):
        """icon from blueprint type, automatically detected"""
        mock_esi.client = EsiClientStub()
        eve_type, _ = EveType.objects.get_or_create_esi(id=950)

        self.assertEqual(
            eve_type.icon_url(256), "https://images.evetech.net/types/950/bp?size=256"
        )

    def test_can_create_icon_url_3(self, mock_esi):
        """icon from regular type, preset as blueprint"""
        mock_esi.client = EsiClientStub()
        eve_type, _ = EveType.objects.get_or_create_esi(id=603)

        self.assertEqual(
            eve_type.icon_url(size=256, is_blueprint=True),
            "https://images.evetech.net/types/603/bp?size=256",
        )

    def test_can_create_icon_url_3a(self, mock_esi):
        """icon from regular type, preset as blueprint"""
        mock_esi.client = EsiClientStub()
        eve_type, _ = EveType.objects.get_or_create_esi(id=603)

        self.assertEqual(
            eve_type.icon_url(size=256, category_id=EveCategoryId.BLUEPRINT),
            "https://images.evetech.net/types/603/bp?size=256",
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_USE_EVESKINSERVER", False)
    def test_can_create_icon_url_5(self, mock_esi):
        """when called for SKIN type, will return dummy SKIN URL with requested size"""
        mock_esi.client = EsiClientStub()
        eve_type, _ = EveType.objects.get_or_create_esi(id=34599)

        self.assertIn("skin_generic_64.png", eve_type.icon_url(size=64))

    @patch(MODELS_PATH + ".EVEUNIVERSE_USE_EVESKINSERVER", False)
    def test_can_create_icon_url_5a(self, mock_esi):
        """when called for SKIN type, will return dummy SKIN URL with requested size"""
        mock_esi.client = EsiClientStub()
        eve_type, _ = EveType.objects.get_or_create_esi(id=34599)

        self.assertIn("skin_generic_32.png", eve_type.icon_url(size=32))

    @patch(MODELS_PATH + ".EVEUNIVERSE_USE_EVESKINSERVER", False)
    def test_can_create_icon_url_5b(self, mock_esi):
        """when called for SKIN type, will return dummy SKIN URL with requested size"""
        mock_esi.client = EsiClientStub()
        eve_type, _ = EveType.objects.get_or_create_esi(id=34599)

        self.assertIn("skin_generic_128.png", eve_type.icon_url(size=128))

    @patch(MODELS_PATH + ".EVEUNIVERSE_USE_EVESKINSERVER", False)
    def test_can_create_icon_url_5c(self, mock_esi):
        """when called for SKIN type and size is invalid, then raise exception"""
        mock_esi.client = EsiClientStub()
        eve_type, _ = EveType.objects.get_or_create_esi(id=34599)

        with self.assertRaises(ValueError):
            eve_type.icon_url(size=512)

        with self.assertRaises(ValueError):
            eve_type.icon_url(size=1024)

        with self.assertRaises(ValueError):
            eve_type.icon_url(size=31)

    @patch(MODELS_PATH + ".EVEUNIVERSE_USE_EVESKINSERVER", False)
    def test_can_create_icon_url_6(self, mock_esi):
        """when called for non SKIN type and SKIN is forced, then return SKIN URL"""
        mock_esi.client = EsiClientStub()
        eve_type, _ = EveType.objects.get_or_create_esi(id=950)

        self.assertIn(
            "skin_generic_128.png",
            eve_type.icon_url(size=128, category_id=EveCategoryId.SKIN),
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_USE_EVESKINSERVER", False)
    def test_can_create_icon_url_7(self, mock_esi):
        """when called for SKIN type and regular is forced, then return regular URL"""
        mock_esi.client = EsiClientStub()
        eve_type, _ = EveType.objects.get_or_create_esi(id=34599)

        self.assertEqual(
            eve_type.icon_url(size=256, category_id=EveCategoryId.STRUCTURE),
            "https://images.evetech.net/types/34599/icon?size=256",
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_USE_EVESKINSERVER", True)
    def test_can_create_icon_url_8(self, mock_esi):
        """
        when called for SKIN type and eveskinserver is enabled,
        then return corresponding eveskinserver URL
        """
        mock_esi.client = EsiClientStub()
        eve_type, _ = EveType.objects.get_or_create_esi(id=34599)

        self.assertEqual(
            eve_type.icon_url(size=256),
            "https://eveskinserver.kalkoken.net/skin/34599/icon?size=256",
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_USE_EVESKINSERVER", True)
    def test_can_create_icon_url_9(self, mock_esi):
        """can use variants"""
        mock_esi.client = EsiClientStub()
        eve_type, _ = EveType.objects.get_or_create_esi(id=603)

        self.assertEqual(
            eve_type.icon_url(size=256, variant=EveType.IconVariant.REGULAR),
            "https://images.evetech.net/types/603/icon?size=256",
        )
        self.assertEqual(
            eve_type.icon_url(size=256, variant=EveType.IconVariant.BPO),
            "https://images.evetech.net/types/603/bp?size=256",
        )
        self.assertEqual(
            eve_type.icon_url(size=256, variant=EveType.IconVariant.BPC),
            "https://images.evetech.net/types/603/bpc?size=256",
        )
        self.assertEqual(
            eve_type.icon_url(size=256, variant=EveType.IconVariant.SKIN),
            "https://eveskinserver.kalkoken.net/skin/603/icon?size=256",
        )


@patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
@patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
@patch(MANAGERS_PATH + ".esi")
class TestEveTypeProfileUrl(NoSocketsTestCase):
    def test_can_url(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        eve_type, _ = EveType.objects.get_or_create_esi(id=603)
        # when
        result = eve_type.profile_url
        # then
        self.assertEqual(result, "https://www.kalkoken.org/apps/eveitems/?typeId=603")


class TestEveUnit(NoSocketsTestCase):
    def test_get_object(self):
        obj = EveUnit.objects.get(id=10)
        self.assertEqual(obj.id, 10)
        self.assertEqual(obj.name, "Speed")


class TestEsiMapping(NoSocketsTestCase):

    maxDiff = None

    def test_single_pk(self):
        mapping = EveCategory._esi_mapping()
        self.assertEqual(len(mapping.keys()), 3)
        self.assertEqual(
            mapping["id"],
            EsiMapping(
                esi_name="category_id",
                is_optional=False,
                is_pk=True,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["name"],
            EsiMapping(
                esi_name="name",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["published"],
            EsiMapping(
                esi_name="published",
                is_optional=False,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )

    def test_with_fk(self):
        mapping = EveConstellation._esi_mapping()
        self.assertEqual(len(mapping.keys()), 6)
        self.assertEqual(
            mapping["id"],
            EsiMapping(
                esi_name="constellation_id",
                is_optional=False,
                is_pk=True,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["name"],
            EsiMapping(
                esi_name="name",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["eve_region"],
            EsiMapping(
                esi_name="region_id",
                is_optional=False,
                is_pk=False,
                is_fk=True,
                related_model=EveRegion,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["position_x"],
            EsiMapping(
                esi_name=("position", "x"),
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["position_y"],
            EsiMapping(
                esi_name=("position", "y"),
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["position_z"],
            EsiMapping(
                esi_name=("position", "z"),
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )

    def test_optional_fields(self):
        mapping = EveAncestry._esi_mapping()
        self.assertEqual(len(mapping.keys()), 6)
        self.assertEqual(
            mapping["id"],
            EsiMapping(
                esi_name="id",
                is_optional=False,
                is_pk=True,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["name"],
            EsiMapping(
                esi_name="name",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["eve_bloodline"],
            EsiMapping(
                esi_name="bloodline_id",
                is_optional=False,
                is_pk=False,
                is_fk=True,
                related_model=EveBloodline,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["description"],
            EsiMapping(
                esi_name="description",
                is_optional=False,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["icon_id"],
            EsiMapping(
                esi_name="icon_id",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["short_description"],
            EsiMapping(
                esi_name="short_description",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
                create_related=True,
            ),
        )

    def test_inline_model(self):
        mapping = EveTypeDogmaEffect._esi_mapping()
        self.assertEqual(len(mapping.keys()), 3)
        self.assertEqual(
            mapping["eve_type"],
            EsiMapping(
                esi_name="eve_type",
                is_optional=False,
                is_pk=True,
                is_fk=True,
                related_model=EveType,
                is_parent_fk=True,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["eve_dogma_effect"],
            EsiMapping(
                esi_name="effect_id",
                is_optional=False,
                is_pk=True,
                is_fk=True,
                related_model=EveDogmaEffect,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["is_default"],
            EsiMapping(
                esi_name="is_default",
                is_optional=False,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
    def test_EveType_mapping(self):
        mapping = EveType._esi_mapping()
        self.assertSetEqual(
            set(mapping.keys()),
            {
                "id",
                "name",
                "description",
                "capacity",
                "eve_group",
                "eve_graphic",
                "icon_id",
                "eve_market_group",
                "mass",
                "packaged_volume",
                "portion_size",
                "radius",
                "published",
                "volume",
            },
        )


@patch(MANAGERS_PATH + ".esi")
class TestEveEntityQuerySet(NoSocketsTestCase):
    def test_can_update_one(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        obj_1001 = create_eve_entity(id=1001)
        entities = EveEntity.objects.all()
        # when
        result = entities.update_from_esi()
        # then
        obj_1001.refresh_from_db()
        self.assertEqual(result, 1)
        self.assertEqual(obj_1001.name, "Bruce Wayne")
        self.assertEqual(obj_1001.category, EveEntity.CATEGORY_CHARACTER)

    def test_can_update_many(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        obj_1001 = create_eve_entity(id=1001)
        obj_1002 = create_eve_entity(id=1002)
        obj_2001 = create_eve_entity(id=2001)
        entities = EveEntity.objects.all()
        # when
        result = entities.update_from_esi()
        # then
        self.assertEqual(result, 3)
        obj_1001.refresh_from_db()
        self.assertEqual(obj_1001.name, "Bruce Wayne")
        self.assertEqual(obj_1001.category, EveEntity.CATEGORY_CHARACTER)
        obj_1002.refresh_from_db()
        self.assertEqual(obj_1002.name, "Peter Parker")
        self.assertEqual(obj_1002.category, EveEntity.CATEGORY_CHARACTER)
        obj_2001.refresh_from_db()
        self.assertEqual(obj_2001.name, "Wayne Technologies")
        self.assertEqual(obj_2001.category, EveEntity.CATEGORY_CORPORATION)

    def test_can_divide_and_conquer(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        obj_1001 = create_eve_entity(id=1001)
        obj_1002 = create_eve_entity(id=1002)
        obj_2001 = create_eve_entity(id=2001)
        create_eve_entity(id=9999)
        entities = EveEntity.objects.all()
        # when
        result = entities.update_from_esi()
        self.assertEqual(result, 3)
        obj_1001.refresh_from_db()
        self.assertEqual(obj_1001.name, "Bruce Wayne")
        self.assertEqual(obj_1001.category, EveEntity.CATEGORY_CHARACTER)
        obj_1002.refresh_from_db()
        self.assertEqual(obj_1002.name, "Peter Parker")
        self.assertEqual(obj_1002.category, EveEntity.CATEGORY_CHARACTER)
        obj_2001.refresh_from_db()
        self.assertEqual(obj_2001.name, "Wayne Technologies")
        self.assertEqual(obj_2001.category, EveEntity.CATEGORY_CORPORATION)

    def test_can_ignore_invalid_ids(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        obj_1001 = create_eve_entity(id=1001)
        create_eve_entity(id=1)
        entities = EveEntity.objects.all()
        # when
        result = entities.update_from_esi()
        # then
        self.assertEqual(result, 1)
        obj_1001.refresh_from_db()
        self.assertEqual(result, 1)
        self.assertEqual(obj_1001.name, "Bruce Wayne")
        self.assertEqual(obj_1001.category, EveEntity.CATEGORY_CHARACTER)


class TestEveEntity(NoSocketsTestCase):
    def test_is_npc_1(self):
        """when entity is NPC character, then return True"""
        obj = EveEntity(id=3019583, category=EveEntity.CATEGORY_CHARACTER)
        self.assertTrue(obj.is_npc)

    def test_is_npc_2(self):
        """when entity is NPC corporation, then return True"""
        obj = EveEntity(id=1000274, category=EveEntity.CATEGORY_CORPORATION)
        self.assertTrue(obj.is_npc)

    def test_is_npc_3(self):
        """when entity is normal character, then return False"""
        obj = EveEntity(id=93330670, category=EveEntity.CATEGORY_CHARACTER)
        self.assertFalse(obj.is_npc)

    def test_is_npc_4(self):
        """when entity is normal corporation, then return False"""
        obj = EveEntity(id=98394960, category=EveEntity.CATEGORY_CORPORATION)
        self.assertFalse(obj.is_npc)

    def test_is_npc_5(self):
        """when entity is normal alliance, then return False"""
        obj = EveEntity(id=99008435, category=EveEntity.CATEGORY_ALLIANCE)
        self.assertFalse(obj.is_npc)

    def test_is_npc_starter_corporation_1(self):
        obj = EveEntity(id=1000165, category=EveEntity.CATEGORY_CORPORATION)
        self.assertTrue(obj.is_npc_starter_corporation)

    def test_is_npc_starter_corporation_2(self):
        obj = EveEntity(id=98394960, category=EveEntity.CATEGORY_CORPORATION)
        self.assertFalse(obj.is_npc_starter_corporation)

    def test_is_npc_starter_corporation_3(self):
        obj = EveEntity(id=1000274, category=EveEntity.CATEGORY_CORPORATION)
        self.assertFalse(obj.is_npc_starter_corporation)

    def test_repr(self):
        # given
        obj = EveEntity(
            id=1001, name="Bruce Wayne", category=EveEntity.CATEGORY_CHARACTER
        )
        # when/then
        self.assertEqual(
            repr(obj), "EveEntity(category='character', id=1001, name='Bruce Wayne')"
        )

    def test_can_create_icon_urls_alliance(self):
        obj = EveEntity(id=3001, category=EveEntity.CATEGORY_ALLIANCE)
        expected = "https://images.evetech.net/alliances/3001/logo?size=128"
        self.assertEqual(obj.icon_url(128), expected)

    def test_can_create_icon_urls_character(self):
        obj = EveEntity(id=1001, category=EveEntity.CATEGORY_CHARACTER)
        expected = "https://images.evetech.net/characters/1001/portrait?size=128"
        self.assertEqual(obj.icon_url(128), expected)

    def test_can_create_icon_urls_corporation(self):
        obj = EveEntity(id=2001, category=EveEntity.CATEGORY_CORPORATION)
        expected = "https://images.evetech.net/corporations/2001/logo?size=128"
        self.assertEqual(obj.icon_url(128), expected)

    def test_can_create_icon_urls_type(self):
        obj = EveEntity(id=603, category=EveEntity.CATEGORY_INVENTORY_TYPE)
        expected = "https://images.evetech.net/types/603/icon?size=128"
        self.assertEqual(obj.icon_url(128), expected)


@patch(MANAGERS_PATH + ".esi")
class TestEveEntityEsi(NoSocketsTestCase):
    def test_can_create_new_from_esi_with_id(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, created = EveEntity.objects.update_or_create_esi(id=1001)
        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, 1001)
        self.assertEqual(obj.name, "Bruce Wayne")
        self.assertEqual(obj.category, EveEntity.CATEGORY_CHARACTER)

    def test_get_or_create_esi_with_id_1(self, mock_esi):
        """when object already exists, then just return it"""
        # given
        mock_esi.client = EsiClientStub()
        obj_1 = create_eve_entity(id=1001, name="New Name")
        # when
        obj_2, created = EveEntity.objects.get_or_create_esi(id=1001)
        # then
        self.assertFalse(created)
        self.assertEqual(obj_1, obj_2)

    def test_get_or_create_esi_with_id_2(self, mock_esi):
        """when object doesn't exist, then fetch it from ESi"""
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, created = EveEntity.objects.get_or_create_esi(id=1001)
        # then
        self.assertTrue(created)
        self.assertEqual(obj.name, "Bruce Wayne")

    def test_get_or_create_esi_with_id_3(self, mock_esi):
        """when ID is invalid, then return an empty object"""
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, created = EveEntity.objects.get_or_create_esi(id=9999)
        # then
        self.assertIsNone(obj)
        self.assertFalse(created)

    def test_get_or_create_esi_with_id_4(self, mock_esi):
        """when object already exists and has not yet been resolved, fetch it from ESI"""
        # given
        mock_esi.client = EsiClientStub()
        create_eve_entity(id=1001)
        # when
        obj, created = EveEntity.objects.get_or_create_esi(id=1001)
        # then
        self.assertFalse(created)
        self.assertEqual(obj.name, "Bruce Wayne")

    def test_can_update_existing_from_esi(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        create_eve_entity(
            id=1001, name="John Doe", category=EveEntity.CATEGORY_CORPORATION
        )
        # when
        obj, created = EveEntity.objects.update_or_create_esi(id=1001)
        # then
        self.assertFalse(created)
        self.assertEqual(obj.id, 1001)
        self.assertEqual(obj.name, "Bruce Wayne")
        self.assertEqual(obj.category, EveEntity.CATEGORY_CHARACTER)

    def test_update_or_create_all_esi_raises_exception(self, _):
        with self.assertRaises(NotImplementedError):
            EveEntity.objects.update_or_create_all_esi()

    def test_can_bulk_update_new_from_esi(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        EveEntity.objects.create(id=1001)
        EveEntity.objects.create(id=2001)
        # when
        result = EveEntity.objects.bulk_update_new_esi()
        # then
        self.assertEqual(result, 2)
        obj = EveEntity.objects.get(id=1001)
        self.assertEqual(obj.id, 1001)
        self.assertEqual(obj.name, "Bruce Wayne")
        self.assertEqual(obj.category, EveEntity.CATEGORY_CHARACTER)
        obj = EveEntity.objects.get(id=2001)
        self.assertEqual(obj.id, 2001)
        self.assertEqual(obj.name, "Wayne Technologies")
        self.assertEqual(obj.category, EveEntity.CATEGORY_CORPORATION)

    def test_bulk_update_all_esi(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        e1 = EveEntity.objects.create(id=1001)
        e2 = EveEntity.objects.create(id=2001)
        # when
        EveEntity.objects.bulk_update_all_esi()
        # then
        e1.refresh_from_db()
        self.assertEqual(e1.name, "Bruce Wayne")
        e2.refresh_from_db()
        self.assertEqual(e2.name, "Wayne Technologies")

    def test_can_resolve_name(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        self.assertEqual(EveEntity.objects.resolve_name(1001), "Bruce Wayne")
        self.assertEqual(EveEntity.objects.resolve_name(2001), "Wayne Technologies")
        self.assertEqual(EveEntity.objects.resolve_name(3001), "Wayne Enterprises")
        self.assertEqual(EveEntity.objects.resolve_name(999), "")
        self.assertEqual(EveEntity.objects.resolve_name(None), "")

    def test_can_fetch_entity_by_name_from_esi(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        result = EveEntity.objects.fetch_by_names_esi(["Bruce Wayne"])
        # then
        self.assertListEqual(list(result), list(EveEntity.objects.filter(id=1001)))

    def test_can_fetch_entities_by_name_from_esi(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        result = EveEntity.objects.fetch_by_names_esi(["Bruce Wayne", "Caldari State"])
        # then
        self.assertListEqual(
            list(result), list(EveEntity.objects.filter(id__in=[500001, 1001]))
        )

    def test_can_fetch_entities_by_name_from_esi_huge(self, mock_esi):
        # given
        def my_endpoint(names):
            characters = [
                {"id": int(name.split("_")[1]), "name": name} for name in names
            ]
            data = {"characters": characters}
            return BravadoOperationStub(data)

        mock_esi.client.Universe.post_universe_ids.side_effect = my_endpoint
        names = [f"dummy_{num + 1001}" for num in range(600)]
        # when
        result = EveEntity.objects.fetch_by_names_esi(names)
        # then
        self.assertEqual(mock_esi.client.Universe.post_universe_ids.call_count, 2)
        self.assertEqual(len(result), 600)

    def test_can_bulk_resolve_name(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        resolver = EveEntity.objects.bulk_resolve_names([1001, 2001, 3001])
        # when
        self.assertEqual(resolver.to_name(1001), "Bruce Wayne")
        self.assertEqual(resolver.to_name(2001), "Wayne Technologies")
        self.assertEqual(resolver.to_name(3001), "Wayne Enterprises")

    def test_is_alliance(self, mock_esi):
        """when entity is an alliance, then return True, else False"""
        mock_esi.client = EsiClientStub()

        obj, _ = EveEntity.objects.update_or_create_esi(id=3001)  # alliance
        self.assertTrue(obj.is_alliance)
        obj, _ = EveEntity.objects.update_or_create_esi(id=1001)  # character
        self.assertFalse(obj.is_alliance)
        obj, _ = EveEntity.objects.update_or_create_esi(id=20000020)  # constellation
        self.assertFalse(obj.is_alliance)
        obj, _ = EveEntity.objects.update_or_create_esi(id=2001)  # corporation
        self.assertFalse(obj.is_alliance)
        obj, _ = EveEntity.objects.update_or_create_esi(id=500001)  # faction
        self.assertFalse(obj.is_alliance)
        obj, _ = EveEntity.objects.update_or_create_esi(id=603)  # inventory type
        self.assertFalse(obj.is_alliance)
        obj, _ = EveEntity.objects.update_or_create_esi(id=10000069)  # region
        self.assertFalse(obj.is_alliance)
        obj, _ = EveEntity.objects.update_or_create_esi(id=30004984)  # solar system
        self.assertFalse(obj.is_alliance)
        obj, _ = EveEntity.objects.update_or_create_esi(id=60015068)  # station
        self.assertFalse(obj.is_alliance)
        obj = EveEntity(id=666)
        self.assertFalse(obj.is_alliance)

    def test_is_character(self, mock_esi):
        """when entity is a character, then return True, else False"""
        mock_esi.client = EsiClientStub()

        obj, _ = EveEntity.objects.update_or_create_esi(id=3001)  # alliance
        self.assertFalse(obj.is_character)
        obj, _ = EveEntity.objects.update_or_create_esi(id=1001)  # character
        self.assertTrue(obj.is_character)
        obj, _ = EveEntity.objects.update_or_create_esi(id=20000020)  # constellation
        self.assertFalse(obj.is_character)
        obj, _ = EveEntity.objects.update_or_create_esi(id=2001)  # corporation
        self.assertFalse(obj.is_character)
        obj, _ = EveEntity.objects.update_or_create_esi(id=500001)  # faction
        self.assertFalse(obj.is_character)
        obj, _ = EveEntity.objects.update_or_create_esi(id=603)  # inventory type
        self.assertFalse(obj.is_character)
        obj, _ = EveEntity.objects.update_or_create_esi(id=10000069)  # region
        self.assertFalse(obj.is_character)
        obj, _ = EveEntity.objects.update_or_create_esi(id=30004984)  # solar system
        self.assertFalse(obj.is_character)
        obj, _ = EveEntity.objects.update_or_create_esi(id=60015068)  # station
        self.assertFalse(obj.is_character)
        obj = EveEntity(id=666)
        self.assertFalse(obj.is_character)

    def test_is_constellation(self, mock_esi):
        """when entity is a constellation, then return True, else False"""
        mock_esi.client = EsiClientStub()

        obj, _ = EveEntity.objects.update_or_create_esi(id=3001)  # alliance
        self.assertFalse(obj.is_constellation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=1001)  # character
        self.assertFalse(obj.is_constellation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=20000020)  # constellation
        self.assertTrue(obj.is_constellation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=2001)  # corporation
        self.assertFalse(obj.is_constellation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=500001)  # faction
        self.assertFalse(obj.is_constellation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=603)  # inventory type
        self.assertFalse(obj.is_constellation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=10000069)  # region
        self.assertFalse(obj.is_constellation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=30004984)  # solar system
        self.assertFalse(obj.is_constellation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=60015068)  # station
        self.assertFalse(obj.is_constellation)
        obj = EveEntity(id=666)
        self.assertFalse(obj.is_constellation)

    def test_is_corporation(self, mock_esi):
        """when entity is a corporation, then return True, else False"""
        mock_esi.client = EsiClientStub()

        obj, _ = EveEntity.objects.update_or_create_esi(id=3001)  # alliance
        self.assertFalse(obj.is_corporation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=1001)  # character
        self.assertFalse(obj.is_corporation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=20000020)  # constellation
        self.assertFalse(obj.is_corporation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=2001)  # corporation
        self.assertTrue(obj.is_corporation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=500001)  # faction
        self.assertFalse(obj.is_corporation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=603)  # inventory type
        self.assertFalse(obj.is_corporation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=10000069)  # region
        self.assertFalse(obj.is_corporation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=30004984)  # solar system
        self.assertFalse(obj.is_corporation)
        obj, _ = EveEntity.objects.update_or_create_esi(id=60015068)  # station
        self.assertFalse(obj.is_corporation)
        obj = EveEntity(id=666)
        self.assertFalse(obj.is_corporation)

    def test_is_faction(self, mock_esi):
        """when entity is a faction, then return True, else False"""
        mock_esi.client = EsiClientStub()

        obj, _ = EveEntity.objects.update_or_create_esi(id=3001)  # alliance
        self.assertFalse(obj.is_faction)
        obj, _ = EveEntity.objects.update_or_create_esi(id=1001)  # character
        self.assertFalse(obj.is_faction)
        obj, _ = EveEntity.objects.update_or_create_esi(id=20000020)  # constellation
        self.assertFalse(obj.is_faction)
        obj, _ = EveEntity.objects.update_or_create_esi(id=2001)  # corporation
        self.assertFalse(obj.is_faction)
        obj, _ = EveEntity.objects.update_or_create_esi(id=500001)  # faction
        self.assertTrue(obj.is_faction)
        obj, _ = EveEntity.objects.update_or_create_esi(id=603)  # inventory type
        self.assertFalse(obj.is_faction)
        obj, _ = EveEntity.objects.update_or_create_esi(id=10000069)  # region
        self.assertFalse(obj.is_faction)
        obj, _ = EveEntity.objects.update_or_create_esi(id=30004984)  # solar system
        self.assertFalse(obj.is_faction)
        obj, _ = EveEntity.objects.update_or_create_esi(id=60015068)  # station
        self.assertFalse(obj.is_faction)
        obj = EveEntity(id=666)
        self.assertFalse(obj.is_faction)

    def test_is_type(self, mock_esi):
        """when entity is an inventory type, then return True, else False"""
        mock_esi.client = EsiClientStub()

        obj, _ = EveEntity.objects.update_or_create_esi(id=3001)  # alliance
        self.assertFalse(obj.is_type)
        obj, _ = EveEntity.objects.update_or_create_esi(id=1001)  # character
        self.assertFalse(obj.is_type)
        obj, _ = EveEntity.objects.update_or_create_esi(id=20000020)  # constellation
        self.assertFalse(obj.is_type)
        obj, _ = EveEntity.objects.update_or_create_esi(id=2001)  # corporation
        self.assertFalse(obj.is_type)
        obj, _ = EveEntity.objects.update_or_create_esi(id=500001)  # faction
        self.assertFalse(obj.is_type)
        obj, _ = EveEntity.objects.update_or_create_esi(id=603)  # inventory type
        self.assertTrue(obj.is_type)
        obj, _ = EveEntity.objects.update_or_create_esi(id=10000069)  # region
        self.assertFalse(obj.is_type)
        obj, _ = EveEntity.objects.update_or_create_esi(id=30004984)  # solar system
        self.assertFalse(obj.is_type)
        obj, _ = EveEntity.objects.update_or_create_esi(id=60015068)  # station
        self.assertFalse(obj.is_type)
        obj = EveEntity(id=666)
        self.assertFalse(obj.is_type)

    def test_is_region(self, mock_esi):
        """when entity is a region, then return True, else False"""
        mock_esi.client = EsiClientStub()

        obj, _ = EveEntity.objects.update_or_create_esi(id=3001)  # alliance
        self.assertFalse(obj.is_region)
        obj, _ = EveEntity.objects.update_or_create_esi(id=1001)  # character
        self.assertFalse(obj.is_region)
        obj, _ = EveEntity.objects.update_or_create_esi(id=20000020)  # constellation
        self.assertFalse(obj.is_region)
        obj, _ = EveEntity.objects.update_or_create_esi(id=2001)  # corporation
        self.assertFalse(obj.is_region)
        obj, _ = EveEntity.objects.update_or_create_esi(id=500001)  # faction
        self.assertFalse(obj.is_region)
        obj, _ = EveEntity.objects.update_or_create_esi(id=603)  # inventory type
        self.assertFalse(obj.is_region)
        obj, _ = EveEntity.objects.update_or_create_esi(id=10000069)  # region
        self.assertTrue(obj.is_region)
        obj, _ = EveEntity.objects.update_or_create_esi(id=30004984)  # solar system
        self.assertFalse(obj.is_region)
        obj, _ = EveEntity.objects.update_or_create_esi(id=60015068)  # station
        self.assertFalse(obj.is_region)
        obj = EveEntity(id=666)
        self.assertFalse(obj.is_region)

    def test_is_solar_system(self, mock_esi):
        """when entity is a solar system, then return True, else False"""
        mock_esi.client = EsiClientStub()

        obj, _ = EveEntity.objects.update_or_create_esi(id=3001)  # alliance
        self.assertFalse(obj.is_solar_system)
        obj, _ = EveEntity.objects.update_or_create_esi(id=1001)  # character
        self.assertFalse(obj.is_solar_system)
        obj, _ = EveEntity.objects.update_or_create_esi(id=20000020)  # constellation
        self.assertFalse(obj.is_solar_system)
        obj, _ = EveEntity.objects.update_or_create_esi(id=2001)  # corporation
        self.assertFalse(obj.is_solar_system)
        obj, _ = EveEntity.objects.update_or_create_esi(id=500001)  # faction
        self.assertFalse(obj.is_solar_system)
        obj, _ = EveEntity.objects.update_or_create_esi(id=603)  # inventory type
        self.assertFalse(obj.is_solar_system)
        obj, _ = EveEntity.objects.update_or_create_esi(id=10000069)  # region
        self.assertFalse(obj.is_solar_system)
        obj, _ = EveEntity.objects.update_or_create_esi(id=30004984)  # solar system
        self.assertTrue(obj.is_solar_system)
        obj, _ = EveEntity.objects.update_or_create_esi(id=60015068)  # station
        self.assertFalse(obj.is_solar_system)
        obj = EveEntity(id=666)
        self.assertFalse(obj.is_solar_system)

    def test_is_station(self, mock_esi):
        """when entity is a station, then return True, else False"""
        mock_esi.client = EsiClientStub()

        obj, _ = EveEntity.objects.update_or_create_esi(id=3001)  # alliance
        self.assertFalse(obj.is_station)
        obj, _ = EveEntity.objects.update_or_create_esi(id=1001)  # character
        self.assertFalse(obj.is_station)
        obj, _ = EveEntity.objects.update_or_create_esi(id=20000020)  # constellation
        self.assertFalse(obj.is_station)
        obj, _ = EveEntity.objects.update_or_create_esi(id=2001)  # corporation
        self.assertFalse(obj.is_station)
        obj, _ = EveEntity.objects.update_or_create_esi(id=500001)  # faction
        self.assertFalse(obj.is_station)
        obj, _ = EveEntity.objects.update_or_create_esi(id=603)  # inventory type
        self.assertFalse(obj.is_station)
        obj, _ = EveEntity.objects.update_or_create_esi(id=10000069)  # region
        self.assertFalse(obj.is_station)
        obj, _ = EveEntity.objects.update_or_create_esi(id=30004984)  # solar system
        self.assertFalse(obj.is_station)
        obj, _ = EveEntity.objects.update_or_create_esi(id=60015068)  # station
        self.assertTrue(obj.is_station)
        obj = EveEntity(id=666)
        self.assertFalse(obj.is_station)


class TestEveEntityProfileUrl(NoSocketsTestCase):
    def test_should_handle_alliance(self):
        # given
        obj = EveEntity.objects.create(
            id=3001, name="Wayne Enterprises", category=EveEntity.CATEGORY_ALLIANCE
        )
        # when/then
        self.assertEqual(
            obj.profile_url, "https://evemaps.dotlan.net/alliance/Wayne_Enterprises"
        )

    def test_should_handle_character(self):
        # given
        obj = EveEntity.objects.create(
            id=1001, name="Bruce Wayne", category=EveEntity.CATEGORY_CHARACTER
        )
        # when/then
        self.assertEqual(obj.profile_url, "https://evewho.com/character/1001")

    def test_should_handle_corporation(self):
        # given
        obj = EveEntity.objects.create(
            id=2001, name="Wayne Technologies", category=EveEntity.CATEGORY_CORPORATION
        )
        # when/then
        self.assertEqual(
            obj.profile_url, "https://evemaps.dotlan.net/corp/Wayne_Technologies"
        )

    def test_should_handle_faction(self):
        # given
        obj = EveEntity.objects.create(
            id=99, name="Amarr Empire", category=EveEntity.CATEGORY_FACTION
        )
        # when/then
        self.assertEqual(
            obj.profile_url, "https://evemaps.dotlan.net/factionwarfare/Amarr_Empire"
        )

    def test_should_handle_inventory_type(self):
        # given
        obj = EveEntity.objects.create(
            id=603, name="Merlin", category=EveEntity.CATEGORY_INVENTORY_TYPE
        )
        # when/then
        self.assertEqual(
            obj.profile_url, "https://www.kalkoken.org/apps/eveitems/?typeId=603"
        )

    def test_should_handle_solar_system(self):
        # given
        obj = EveEntity.objects.create(
            id=30004984, name="Abune", category=EveEntity.CATEGORY_SOLAR_SYSTEM
        )
        # when/then
        self.assertEqual(obj.profile_url, "https://evemaps.dotlan.net/system/Abune")

    def test_should_handle_station(self):
        # given
        obj = EveEntity.objects.create(
            id=60003760,
            name="Jita IV - Moon 4 - Caldari Navy Assembly Plant",
            category=EveEntity.CATEGORY_STATION,
        )
        # when/then
        self.assertEqual(
            obj.profile_url,
            "https://evemaps.dotlan.net/station/Jita_IV_-_Moon_4_-_Caldari_Navy_Assembly_Plant",
        )

    def test_should_return_empty_string_for_undefined_category(self):
        # given
        obj = EveEntity.objects.create(
            id=99, name="Wayne Technologies", category=EveEntity.CATEGORY_CONSTELLATION
        )
        self.assertEqual(obj.profile_url, "")


@patch(MANAGERS_PATH + ".esi")
class TestEveEntityBulkCreateEsi(NoSocketsTestCase):
    def setUp(self):
        EveEntity.objects.all().delete()

    def test_create_new_entities(self, mock_esi):
        mock_esi.client = EsiClientStub()

        result = EveEntity.objects.bulk_create_esi(ids=[1001, 2001])
        self.assertEqual(result, 2)

        obj = EveEntity.objects.get(id=1001)
        self.assertEqual(obj.id, 1001)
        self.assertEqual(obj.name, "Bruce Wayne")
        self.assertEqual(obj.category, EveEntity.CATEGORY_CHARACTER)

        obj = EveEntity.objects.get(id=2001)
        self.assertEqual(obj.id, 2001)
        self.assertEqual(obj.name, "Wayne Technologies")
        self.assertEqual(obj.category, EveEntity.CATEGORY_CORPORATION)

    def test_create_only_non_existing_entities(self, mock_esi):
        mock_esi.client = EsiClientStub()

        EveEntity.objects.create(
            id=1001, name="Bruce Wayne", category=EveEntity.CATEGORY_CHARACTER
        )
        result = EveEntity.objects.bulk_create_esi(ids=[1001, 2001])
        self.assertEqual(result, 1)

        obj = EveEntity.objects.get(id=1001)
        self.assertEqual(obj.id, 1001)
        self.assertEqual(obj.name, "Bruce Wayne")
        self.assertEqual(obj.category, EveEntity.CATEGORY_CHARACTER)

        obj = EveEntity.objects.get(id=2001)
        self.assertEqual(obj.id, 2001)
        self.assertEqual(obj.name, "Wayne Technologies")
        self.assertEqual(obj.category, EveEntity.CATEGORY_CORPORATION)

    def test_entities_without_name_will_be_refetched(self, mock_esi):
        mock_esi.client = EsiClientStub()

        EveEntity.objects.create(id=1001, category=EveEntity.CATEGORY_CORPORATION)
        result = EveEntity.objects.bulk_create_esi(ids=[1001, 2001])
        self.assertEqual(result, 2)

        obj = EveEntity.objects.get(id=1001)
        self.assertEqual(obj.id, 1001)
        self.assertEqual(obj.name, "Bruce Wayne")
        self.assertEqual(obj.category, EveEntity.CATEGORY_CHARACTER)

        obj = EveEntity.objects.get(id=2001)
        self.assertEqual(obj.id, 2001)
        self.assertEqual(obj.name, "Wayne Technologies")
        self.assertEqual(obj.category, EveEntity.CATEGORY_CORPORATION)
