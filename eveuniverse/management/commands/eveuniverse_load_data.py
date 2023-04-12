import logging
from enum import Enum

from celery import chain
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
    TYPES = "types"


class Command(BaseCommand):
    help = "Loads large sets of data from ESI into local database"

    def add_arguments(self, parser):
        parser.add_argument(TOKEN_AREA, nargs="+", choices=[o.value for o in Area])
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

        my_tasks = []
        self.stdout.write(
            "This command will load the following from ESI and store it locally::"
        )
        if Area.MAP in options[TOKEN_AREA]:
            self.stdout.write("- all regions, constellations and solar systems")
            my_tasks.append(tasks.load_map.si())

        if Area.TYPES in options[TOKEN_AREA]:
            self.stdout.write("- all types")
            my_tasks.append(tasks.load_all_types.si())

        else:  # TYPES is a superset which includes SHIPS and STRUCTURES
            if Area.SHIPS in options[TOKEN_AREA]:
                self.stdout.write("- all ship types")
                my_tasks.append(tasks.load_ship_types.si())

            if Area.STRUCTURES in options[TOKEN_AREA]:
                self.stdout.write("- all structure types")
                my_tasks.append(tasks.load_structure_types.si())

        if not my_tasks:
            raise NotImplementedError("No implemented area selected.")

        additional_objects = tasks._eve_object_names_to_be_loaded()
        if additional_objects:
            self.stdout.write(
                f"- the following related entities: {','.join(additional_objects)}"
            )
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
