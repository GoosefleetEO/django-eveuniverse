import logging
from enum import Enum

from celery import chain
from django.core.management.base import BaseCommand

from eveuniverse import __title__, tasks
from eveuniverse.core.esitools import is_esi_online
from eveuniverse.models import EveType, EveUniverseEntityModel
from eveuniverse.utils import LoggerAddTag

from . import get_input

logger = LoggerAddTag(logging.getLogger(__name__), __title__)

TOKEN_TOPIC = "topic"


class Topic(str, Enum):
    """Topic to load data for."""

    MAP = "map"
    SHIPS = "ships"
    STRUCTURES = "structures"
    TYPES = "types"


class Command(BaseCommand):
    help = "Load large sets of data from ESI into local database for selected topics"

    def add_arguments(self, parser):
        parser.add_argument(
            TOKEN_TOPIC,
            nargs="+",
            choices=[o.value for o in Topic],
            help="Topic(s) to load data for",
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_true",
            help="Do NOT prompt the user for input of any kind.",
        )
        parser.add_argument(
            "--types-enabled-sections",
            nargs="+",
            default=None,
            choices=[o.value for o in EveType.Section],
            help="List of enabled sections for types topic",
        )

    def handle(self, *args, **options):
        self.stdout.write("Eve Universe - Data Loader")
        self.stdout.write("==========================")
        self.stdout.write("")

        if not is_esi_online():
            self.stdout.write(
                "ESI does not appear to be online at this time. Please try again later."
            )
            self.stdout.write(self.style.WARNING("Aborted"))
            return

        my_tasks = []
        self.stdout.write(
            "This command will fetch the following data from ESI and store it locally:"
        )
        if Topic.TYPES in options[TOKEN_TOPIC]:
            text, enabled_sections = self._text_with_enabled_sections(
                "- all types", options["types_enabled_sections"]
            )
            self.stdout.write(text)
            my_tasks.append(tasks.load_all_types.si(enabled_sections=enabled_sections))

        else:  # TYPES is a superset which includes SHIPS and STRUCTURES
            if Topic.SHIPS in options[TOKEN_TOPIC]:
                text, enabled_sections = self._text_with_enabled_sections(
                    "- ship types"
                )
                self.stdout.write(text)
                my_tasks.append(tasks.load_ship_types.si())

            if Topic.STRUCTURES in options[TOKEN_TOPIC]:
                text, enabled_sections = self._text_with_enabled_sections(
                    "- structure types"
                )
                self.stdout.write(text)
                my_tasks.append(tasks.load_structure_types.si())

        if Topic.MAP in options[TOKEN_TOPIC]:
            text, enabled_sections = self._text_with_enabled_sections(
                "- all regions, constellations and solar systems"
            )
            self.stdout.write(text)

            my_tasks.append(tasks.load_map.si())

        if not my_tasks:
            raise NotImplementedError("No implemented topic selected.")

        self.stdout.write("")
        self.stdout.write(
            "Note that this process can take some time to complete. "
            "It will create many tasks to load the data and "
            "you can watch the progress on the dashboard. "
            "It is likely finished as soon as the task queue is empty again."
        )
        if not options["noinput"]:
            user_input = get_input("Are you sure you want to proceed? (Y/n)? ")
        else:
            user_input = "y"
        if user_input.lower() != "n":
            chain(my_tasks).delay()
            self.stdout.write(self.style.SUCCESS("Data load started!"))
        else:
            self.stdout.write(self.style.WARNING("Aborted"))

    def _text_with_enabled_sections(self, text, enabled_sections=None):
        effective_sections = EveUniverseEntityModel.determine_effective_sections(
            enabled_sections
        )
        if effective_sections:
            new_text = f"{text} including these sections: {', '.join(sorted(effective_sections))}"
        else:
            new_text = text
        return new_text, effective_sections
