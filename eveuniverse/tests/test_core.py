from unittest.mock import Mock, patch

import requests_mock
from bravado.exception import HTTPInternalServerError
from requests.exceptions import HTTPError

from django.core.cache import cache
from django.test import TestCase

from ..constants import EVE_GROUP_ID_MOON
from ..core import esitools, eveimageserver, evemicros, eveskinserver
from ..utils import NoSocketsTestCase
from .testdata.esi import EsiClientStub


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


items = {
    40170698: {
        "itemID": 40170698,
        "itemName": "Colelie VI - Asteroid Belt 1",
        "typeID": 15,
        "typeName": "Asteroid Belt",
        "groupID": 9,
        "groupName": "Asteroid Belt",
        "solarSystemID": "30002682",
        "regionID": 10000032,
        "constellationID": 10000032,
        "x": "392074567680",
        "y": "78438850560",
        "z": "-199546920960",
        "security": 0.51238882808862296069918329521897248923778533935546875,
        "distance": 4.69249999999999989341858963598497211933135986328125,
        "distanceKm": 701983769,
    },
    50011472: {
        "itemID": 50011472,
        "itemName": "Stargate (Deltole)",
        "typeID": 3875,
        "typeName": "Stargate (Gallente System)",
        "groupID": 10,
        "groupName": "Stargate",
        "solarSystemID": "30002682",
        "regionID": 10000032,
        "constellationID": 10000032,
        "x": "390678650880",
        "y": "78437130240",
        "z": "-199573463040",
        "security": 0.51238882808862296069918329521897248923778533935546875,
        "distance": 4.6958999999999999630517777404747903347015380859375,
        "distanceKm": 702495020,
    },
    40170697: {
        "itemID": 40170697,
        "itemName": "Colelie VI",
        "typeID": 13,
        "typeName": "Planet (Gas)",
        "groupID": 7,
        "groupName": "Planet",
        "solarSystemID": "30002682",
        "regionID": 10000032,
        "constellationID": 10000032,
        "x": "390691127743",
        "y": "78438936622",
        "z": "-199521990101",
        "security": 0.51238882808862296069918329521897248923778533935546875,
        "distance": 4.69620000000000015205614545266143977642059326171875,
        "distanceKm": 702535753,
    },
    40170699: {
        "itemID": 40170699,
        "itemName": "Colelie VI - Moon 1",
        "typeID": 14,
        "typeName": "Moon",
        "groupID": 8,
        "groupName": "Moon",
        "solarSystemID": "30002682",
        "regionID": 10000032,
        "constellationID": 10000032,
        "x": "390796699186",
        "y": "78460132168",
        "z": "-199482549699",
        "security": 0.51238882808862296069918329521897248923778533935546875,
        "distance": 4.69620000000000015205614545266143977642059326171875,
        "distanceKm": 702535998,
    },
    40170700: {
        "itemID": 40170700,
        "itemName": "Colelie VI - Moon 2",
        "typeID": 14,
        "typeName": "Moon",
        "groupID": 8,
        "groupName": "Moon",
        "solarSystemID": "30002682",
        "regionID": 10000032,
        "constellationID": 10000032,
        "x": "390287025280",
        "y": "78357805096",
        "z": "-199058647578",
        "security": 0.51238882808862296069918329521897248923778533935546875,
        "distance": 4.699799999999999755573298898525536060333251953125,
        "distanceKm": 703071835,
    },
    40170701: {
        "itemID": 40170701,
        "itemName": "Colelie VI - Moon 3",
        "typeID": 14,
        "typeName": "Moon",
        "groupID": 8,
        "groupName": "Moon",
        "solarSystemID": "30002682",
        "regionID": 10000032,
        "constellationID": 10000032,
        "x": "390135687385",
        "y": "78327421033",
        "z": "-198566076258",
        "security": 0.51238882808862296069918329521897248923778533935546875,
        "distance": 4.70300000000000029132252166164107620716094970703125,
        "distanceKm": 703551499,
    },
}


def create_item(item_id):
    return items[item_id]


def create_request(*item_ids, ok=True):
    return {
        "ok": ok,
        "result": [create_item(item_id) for item_id in item_ids],
    }


@requests_mock.Mocker()
class TestEveMicrosNearestCelestial(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def test_should_return_item_from_api(self, requests_mocker):
        # given
        requests_mocker.register_uri(
            "GET",
            url="https://www.kalkoken.org/apps/evemicros/eveUniverse.php?nearestCelestials=30002682,660502472160,-130687672800,-813545103840",
            json=create_request(40170698, 50011472, 40170697),
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
            json=create_request(40170698, 50011472, 40170697),
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
            json=create_request(),
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
            json=create_request(40170698, 50011472, ok=False),
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
            json=create_request(40170698, 50011472, 40170697, 40170699),
        )
        # when
        result = evemicros.nearest_celestial(
            solar_system_id=30002682,
            x=660502472160,
            y=-130687672800,
            z=-813545103840,
            group_id=EVE_GROUP_ID_MOON,
        )
        # then
        self.assertEqual(result.id, 40170699)
