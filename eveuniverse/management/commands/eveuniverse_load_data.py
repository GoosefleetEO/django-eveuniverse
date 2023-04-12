import logging
from enum import Enum

from django.core.management.base import BaseCommand
from eveuniverse import __title__, tasks
from eveuniverse.core.esitools import is_esi_online
from eveuniverse.utils import LoggerAddTag

from . import get_input

logger = LoggerAddTag(logging.getLogger(__name__), __title__)

TOKEN_AREA = "area"


class Area(str, Enum):
    """Area to load data for."""

    MAP = "map"
    SHIPS = "ships"
    STRUCTURES = "structures"


class Command(BaseCommand):
    help = "Loads large sets of data from ESI into local database"

    def add_arguments(self, parser):
        parser.add_argument(
            TOKEN_AREA,
            choices=[Area.MAP.value, Area.SHIPS.value, Area.STRUCTURES.value],
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_true",
            help="Do NOT prompt the user for input of any kind.",
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

        if options[TOKEN_AREA] == Area.MAP:
            text = (
                "This command will start loading the entire Eve Universe map with "
                "regions, constellations and solar systems from ESI and store it "
                "locally. "
            )
            my_task = tasks.load_map

        elif options[TOKEN_AREA] == Area.SHIPS:
            text = "This command will load all ship types from ESI."
            my_task = tasks.load_ship_types

        elif options[TOKEN_AREA] == Area.STRUCTURES:
            text = "This command will load all structure types from ESI."
            my_task = tasks.load_structure_types

        else:
            raise RuntimeError("This exception should be unreachable")

        self.stdout.write(text)

        additional_objects = tasks._eve_object_names_to_be_loaded()
        if additional_objects:
            self.stdout.write(
                "It will also load the following additional entities when related to "
                "objects loaded for the app: "
                f"{','.join(additional_objects)}"
            )
        self.stdout.write(
            "Note that this process can take a while to complete "
            "and may cause some significant load to your system."
        )
        if not options["noinput"]:
            user_input = get_input("Are you sure you want to proceed? (Y/n)? ")
        else:
            user_input = "y"
        if user_input.lower() != "n":
            self.stdout.write("Starting update. Please stand by.")
            my_task.delay()
            self.stdout.write(self.style.SUCCESS("Load started!"))
        else:
            self.stdout.write(self.style.WARNING("Aborted"))
