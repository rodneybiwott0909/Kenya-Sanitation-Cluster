import csv
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from clustering.county_master import COUNTIES
from clustering.models import County
from clustering.services import import_counties_csv, ImportErrorList


class Command(BaseCommand):
    help = "Create the 47 counties (names, codes, regions) and optionally import indicator values from a CSV."

    def add_arguments(self, parser):
        parser.add_argument("--csv", help="Path to a CSV of real indicator data (KNBS/KDHS/JMP).")

    def handle(self, *args, **opts):
        for code, name, region, asal in COUNTIES:
            County.objects.update_or_create(code=code, defaults={"name": name, "region": region, "is_asal": asal})
        self.stdout.write(self.style.SUCCESS("47 counties ready."))
        if opts["csv"]:
            try:
                with open(opts["csv"], "rb") as fh:
                    n = import_counties_csv(fh)
                self.stdout.write(self.style.SUCCESS(f"Imported indicators for {n} rows."))
            except ImportErrorList as e:
                for err in e.errors:
                    self.stderr.write(err)
