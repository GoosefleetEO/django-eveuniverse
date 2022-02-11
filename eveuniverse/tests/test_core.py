from unittest.mock import Mock, patch

import requests_mock
from bravado.exception import HTTPInternalServerError
from requests.exceptions import HTTPError

from django.core.cache import cache
from django.test import TestCase

from ..constants import EveGroupId
from ..core import (
    dotlan,
    esitools,
    eveimageserver,
    eveitems,
    evemicros,
    eveskinserver,
    evewho,
    evexml,
    zkillboard,
)
from ..models import EveEntity
from ..utils import NoSocketsTestCase
from .testdata.esi import EsiClientStub
from .testdata.factories import create_eve_entity, create_evemicros_request


class TestDotlan(TestCase):
    def test_alliance_url(self):
        self.assertEqual(
            dotlan.alliance_url("Wayne Enterprices"),
            "https://evemaps.dotlan.net/alliance/Wayne_Enterprices",
        )

    def test_corporation_url(self):
        self.assertEqual(
            dotlan.corporation_url("Wayne Technology"),
            "https://evemaps.dotlan.net/corp/Wayne_Technology",
        )
        self.assertEqual(
            dotlan.corporation_url("Crédit Agricole"),
            "https://evemaps.dotlan.net/corp/Cr%C3%A9dit_Agricole",
        )

    def test_faction_url(self):
        self.assertEqual(
            dotlan.faction_url("Amarr Empire"),
            "https://evemaps.dotlan.net/factionwarfare/Amarr_Empire",
        )

    def test_region_url(self):
        self.assertEqual(
            dotlan.region_url("Black Rise"), "https://evemaps.dotlan.net/map/Black_Rise"
        )

    def test_solar_system_url(self):
        self.assertEqual(
            dotlan.solar_system_url("Jita"), "https://evemaps.dotlan.net/system/Jita"
        )

    def test_station_url(self):
        self.assertEqual(
            dotlan.station_url("Rakapas V - Home Guard Assembly Plant"),
            "https://evemaps.dotlan.net/station/Rakapas_V_-_Home_Guard_Assembly_Plant",
        )


class TestEveImageServer(TestCase):
    """unit test for eveimageserver"""

    def test_sizes(self):
        self.assertEqual(
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.CHARACTER, 42
            ),
            "https://images.evetech.net/characters/42/portrait?size=32",
        )
        self.assertEqual(
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.CHARACTER, 42, size=32
            ),
            "https://images.evetech.net/characters/42/portrait?size=32",
        )
        self.assertEqual(
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.CHARACTER, 42, size=64
            ),
            "https://images.evetech.net/characters/42/portrait?size=64",
        )
        self.assertEqual(
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.CHARACTER, 42, size=128
            ),
            "https://images.evetech.net/characters/42/portrait?size=128",
        )
        self.assertEqual(
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.CHARACTER, 42, size=256
            ),
            "https://images.evetech.net/characters/42/portrait?size=256",
        )
        self.assertEqual(
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.CHARACTER, 42, size=512
            ),
            "https://images.evetech.net/characters/42/portrait?size=512",
        )
        self.assertEqual(
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.CHARACTER, 42, size=1024
            ),
            "https://images.evetech.net/characters/42/portrait?size=1024",
        )
        with self.assertRaises(ValueError):
            eveimageserver._eve_entity_image_url("corporation", 42, size=-5)

        with self.assertRaises(ValueError):
            eveimageserver._eve_entity_image_url("corporation", 42, size=0)

        with self.assertRaises(ValueError):
            eveimageserver._eve_entity_image_url("corporation", 42, size=31)

        with self.assertRaises(ValueError):
            eveimageserver._eve_entity_image_url("corporation", 42, size=1025)

        with self.assertRaises(ValueError):
            eveimageserver._eve_entity_image_url("corporation", 42, size=2048)

    def test_variant(self):
        self.assertEqual(
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.CHARACTER,
                42,
                variant=eveimageserver.ImageVariant.PORTRAIT,
            ),
            "https://images.evetech.net/characters/42/portrait?size=32",
        )
        self.assertEqual(
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.ALLIANCE,
                42,
                variant=eveimageserver.ImageVariant.LOGO,
            ),
            "https://images.evetech.net/alliances/42/logo?size=32",
        )
        with self.assertRaises(ValueError):
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.CHARACTER,
                42,
                variant=eveimageserver.ImageVariant.LOGO,
            )

    def test_categories(self):
        self.assertEqual(
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.ALLIANCE, 42
            ),
            "https://images.evetech.net/alliances/42/logo?size=32",
        )
        self.assertEqual(
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.CORPORATION, 42
            ),
            "https://images.evetech.net/corporations/42/logo?size=32",
        )
        self.assertEqual(
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.CHARACTER, 42
            ),
            "https://images.evetech.net/characters/42/portrait?size=32",
        )
        with self.assertRaises(ValueError):
            eveimageserver._eve_entity_image_url("invalid", 42)

    def test_tenants(self):
        self.assertEqual(
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.CHARACTER,
                42,
                tenant=eveimageserver.EsiTenant.TRANQUILITY,
            ),
            "https://images.evetech.net/characters/42/portrait?size=32&tenant=tranquility",
        )
        with self.assertRaises(ValueError):
            eveimageserver._eve_entity_image_url(
                eveimageserver.EsiCategory.CHARACTER, 42, tenant="xxx"
            )

    def test_alliance_logo_url(self):
        expected = "https://images.evetech.net/alliances/42/logo?size=128"
        self.assertEqual(eveimageserver.alliance_logo_url(42, 128), expected)

    def test_corporation_logo_url(self):
        expected = "https://images.evetech.net/corporations/42/logo?size=128"
        self.assertEqual(eveimageserver.corporation_logo_url(42, 128), expected)

    def test_character_portrait_url(self):
        expected = "https://images.evetech.net/characters/42/portrait?size=128"
        self.assertEqual(eveimageserver.character_portrait_url(42, 128), expected)

    def test_faction_logo_url(self):
        expected = "https://images.evetech.net/corporations/42/logo?size=128"
        self.assertEqual(eveimageserver.faction_logo_url(42, 128), expected)

    def test_type_icon_url(self):
        expected = "https://images.evetech.net/types/42/icon?size=128"
        self.assertEqual(eveimageserver.type_icon_url(42, 128), expected)

    def test_type_render_url(self):
        expected = "https://images.evetech.net/types/42/render?size=128"
        self.assertEqual(eveimageserver.type_render_url(42, 128), expected)

    def test_type_bp_url(self):
        expected = "https://images.evetech.net/types/42/bp?size=128"
        self.assertEqual(eveimageserver.type_bp_url(42, 128), expected)

    def test_type_bpc_url(self):
        expected = "https://images.evetech.net/types/42/bpc?size=128"
        self.assertEqual(eveimageserver.type_bpc_url(42, 128), expected)


class TestEveSkinServer(TestCase):
    """unit test for eveskinserver"""

    def test_default(self):
        """when called without size, will return url with default size"""
        self.assertEqual(
            eveskinserver.type_icon_url(42),
            "https://eveskinserver.kalkoken.net/skin/42/icon?size=32",
        )

    def test_valid_size(self):
        """when called with valid size, will return url with size"""
        self.assertEqual(
            eveskinserver.type_icon_url(42, size=64),
            "https://eveskinserver.kalkoken.net/skin/42/icon?size=64",
        )

    def test_invalid_size(self):
        """when called with invalid size, will raise exception"""
        with self.assertRaises(ValueError):
            eveskinserver.type_icon_url(42, size=22)


@requests_mock.Mocker()
class TestEveMicrosNearestCelestial(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def test_should_return_item_from_api(self, requests_mocker):
        # given
        requests_mocker.register_uri(
            "GET",
            url="https://www.kalkoken.org/apps/evemicros/eveUniverse.php?nearestCelestials=30002682,660502472160,-130687672800,-813545103840",
            json=create_evemicros_request(40170698, 50011472, 40170697),
        )
        # when
        result = evemicros.nearest_celestial(
            solar_system_id=30002682, x=660502472160, y=-130687672800, z=-813545103840
        )
        # then
        self.assertEqual(result.id, 40170698)
        self.assertEqual(result.name, "Colelie VI - Asteroid Belt 1")
        self.assertEqual(result.type_id, 15)
        self.assertEqual(result.distance, 701983769)
        self.assertEqual(requests_mocker.call_count, 1)

    def test_should_return_item_from_cache(self, requests_mocker):
        # given
        requests_mocker.register_uri(
            "GET",
            url="https://www.kalkoken.org/apps/evemicros/eveUniverse.php?nearestCelestials=99,1,2,3",
            json=create_evemicros_request(40170698, 50011472, 40170697),
        )
        evemicros.nearest_celestial(solar_system_id=99, x=1, y=2, z=3)
        # when
        result = evemicros.nearest_celestial(solar_system_id=99, x=1, y=2, z=3)
        # then
        self.assertEqual(result.id, 40170698)
        self.assertEqual(requests_mocker.call_count, 1)

    def test_should_return_none_if_nothing_found(self, requests_mocker):
        # given
        requests_mocker.register_uri(
            "GET",
            url="https://www.kalkoken.org/apps/evemicros/eveUniverse.php?nearestCelestials=30002682,1,2,3",
            json=create_evemicros_request(),
        )
        # when
        result = evemicros.nearest_celestial(solar_system_id=30002682, x=1, y=2, z=3)
        # then
        self.assertIsNone(result)

    def test_should_return_none_if_api_reports_error(self, requests_mocker):
        # given
        requests_mocker.register_uri(
            "GET",
            url="https://www.kalkoken.org/apps/evemicros/eveUniverse.php?nearestCelestials=30002682,1,2,3",
            json=create_evemicros_request(40170698, 50011472, ok=False),
        )
        # when
        result = evemicros.nearest_celestial(solar_system_id=30002682, x=1, y=2, z=3)
        # then
        self.assertIsNone(result)

    def test_should_raise_exception_for_http_errors(self, requests_mocker):
        # given
        requests_mocker.register_uri(
            "GET",
            url="https://www.kalkoken.org/apps/evemicros/eveUniverse.php?nearestCelestials=30002682,1,2,3",
            status_code=500,
        )
        # when
        with self.assertRaises(HTTPError):
            evemicros.nearest_celestial(solar_system_id=30002682, x=1, y=2, z=3)

    def test_should_return_moon_from_api(self, requests_mocker):
        # given
        requests_mocker.register_uri(
            "GET",
            url="https://www.kalkoken.org/apps/evemicros/eveUniverse.php?nearestCelestials=30002682,660502472160,-130687672800,-813545103840",
            json=create_evemicros_request(40170698, 50011472, 40170697, 40170699),
        )
        # when
        result = evemicros.nearest_celestial(
            solar_system_id=30002682,
            x=660502472160,
            y=-130687672800,
            z=-813545103840,
            group_id=EveGroupId.MOON,
        )
        # then
        self.assertEqual(result.id, 40170699)


class TestEveItems(TestCase):
    def test_type_url(self):
        self.assertEqual(
            eveitems.type_url(603), "https://www.kalkoken.org/apps/eveitems/?typeId=603"
        )


class TestEveWho(TestCase):
    def test_alliance_url(self):
        self.assertEqual(
            evewho.alliance_url(12345678), "https://evewho.com/alliance/12345678"
        )

    def test_corporation_url(self):
        self.assertEqual(
            evewho.corporation_url(12345678), "https://evewho.com/corporation/12345678"
        )

    def test_character_url(self):
        self.assertEqual(
            evewho.character_url(12345678), "https://evewho.com/character/12345678"
        )


class TestEveXml(NoSocketsTestCase):
    def test_should_remove_loc_tag_1(self):
        input = "<loc>Character</loc>"
        expected = "Character"
        self.assertHTMLEqual(evexml.remove_loc_tag(input), expected)

    def test_should_remove_loc_tag_2(self):
        input = "Character"
        expected = "Character"
        self.assertHTMLEqual(evexml.remove_loc_tag(input), expected)

    def test_should_detect_url(self):
        self.assertTrue(evexml.is_url("https://www.example.com/bla"))

    def test_should_detect_non_url(self):
        self.assertFalse(evexml.is_url("no-url"))

    @patch("eveuniverse.managers.esi")
    def test_should_convert_links(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        create_eve_entity(
            id=1001, name="Bruce Wayne", category=EveEntity.CATEGORY_CHARACTER
        )
        create_eve_entity(
            id=2001, name="Wayne Technologies", category=EveEntity.CATEGORY_CORPORATION
        )
        create_eve_entity(
            id=3001, name="Wayne Enterprises", category=EveEntity.CATEGORY_ALLIANCE
        )
        create_eve_entity(
            id=30004984, name="Abune", category=EveEntity.CATEGORY_SOLAR_SYSTEM
        )
        create_eve_entity(
            id=60003760,
            name="Jita IV - Moon 4 - Caldari Navy Assembly Plant",
            category=EveEntity.CATEGORY_STATION,
        )
        my_tests = [
            (
                "Alliance",
                "showinfo:16159//3001",
                "https://evemaps.dotlan.net/alliance/Wayne_Enterprises",
            ),
            ("Character", "showinfo:1376//1001", "https://evewho.com/character/1001"),
            (
                "Corporation",
                "showinfo:2//2001",
                "https://evemaps.dotlan.net/corp/Wayne_Technologies",
            ),
            (
                "Killmail",
                "killReport:84900666:9e6fe9e5392ff0cfc6ab956677dbe1deb69c4b04",
                "https://zkillboard.com/kill/84900666/",
            ),
            (
                "Solar System",
                "showinfo:5//30004984",
                "https://evemaps.dotlan.net/system/Abune",
            ),
            (
                "Station",
                "showinfo:52678//60003760",
                "https://evemaps.dotlan.net/station/Jita_IV_-_Moon_4_-_Caldari_Navy_Assembly_Plant",
            ),
            (
                "Inventory Type",
                "showinfo:603",
                "https://www.kalkoken.org/apps/eveitems/?typeId=603",
            ),
            ("Valid URL", "https://www.example.com", "https://www.example.com"),
            (
                "Not support eve link 1",
                "fitting:11987:2048;1:1952;1:26914;2:31366;1:16487;2:31059;1:19057;2:18867;1:18710;1:18871;1:12058;1:31900;1:41155;1::",
                "",
            ),
            (
                "Not support eve link 2",
                "hyperNet:9ff5fa81-942e-49c2-9469-623b2abcb05d",
                "",
            ),
            ("Invalid URL", "not-valid", ""),
            (
                "Unsuported eve links",
                'showinfo:35825//1000000000001">Amamake - Test Structure Alpha',
                "",
            ),
        ]
        for test, input, expected in my_tests:
            with self.subTest(test=test):
                self.assertEqual(evexml.eve_link_to_url(input), expected)


@patch("eveuniverse.core.esitools.esi")
class TestIsEsiOnline(NoSocketsTestCase):
    def test_is_online(self, mock_esi):
        mock_esi.client = EsiClientStub()

        self.assertTrue(esitools.is_esi_online())

    def test_is_offline(self, mock_esi):
        mock_esi.client.Status.get_status.side_effect = HTTPInternalServerError(
            Mock(**{"response.status_code": 500})
        )

        self.assertFalse(esitools.is_esi_online())


class TestZkillboard(TestCase):
    def test_alliance_url(self):
        self.assertEqual(
            zkillboard.alliance_url(12345678),
            "https://zkillboard.com/alliance/12345678/",
        )

    def test_corporation_url(self):
        self.assertEqual(
            zkillboard.corporation_url(12345678),
            "https://zkillboard.com/corporation/12345678/",
        )

    def test_character_url(self):
        self.assertEqual(
            zkillboard.character_url(12345678),
            "https://zkillboard.com/character/12345678/",
        )

    def test_killmail_url(self):
        self.assertEqual(
            zkillboard.killmail_url(12345678), "https://zkillboard.com/kill/12345678/"
        )

    def test_region_url(self):
        self.assertEqual(
            zkillboard.region_url(12345678), "https://zkillboard.com/region/12345678/"
        )

    def test_solar_system_url(self):
        self.assertEqual(
            zkillboard.solar_system_url(12345678),
            "https://zkillboard.com/system/12345678/",
        )
