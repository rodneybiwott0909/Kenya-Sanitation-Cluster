import numpy as np
from django.core.management.base import BaseCommand
from clustering.county_master import COUNTIES
from clustering.models import County


class Command(BaseCommand):
    help = "Fill counties with SYNTHETIC indicator values so the pipeline can be tested. NOT real data."

    def handle(self, *args, **opts):
        rng = np.random.default_rng(42)
        for code, name, region, asal in COUNTIES:
            if name == "Nairobi" or name == "Mombasa":
                base = [92, 2, 90, 70, 20, 95]
            elif asal:
                base = [35, 40, 50, 25, 60, 15]
            elif region in {"Central", "Western", "Nyanza"}:
                base = [75, 6, 75, 45, 35, 25]
            else:
                base = [60, 15, 65, 35, 40, 25]
            v = np.clip(np.array(base) + rng.normal(0, 6, 6), 0, 100).round(1)
            County.objects.update_or_create(code=code, defaults=dict(
                name=name, region=region, is_asal=asal, improved_sanitation_pct=v[0], open_defecation_pct=v[1],
                improved_water_pct=v[2], handwashing_pct=v[3], poverty_rate_pct=v[4], urban_pop_pct=v[5],
                source="SYNTHETIC DEMO - replace with KNBS/KDHS data"))
        self.stdout.write(self.style.WARNING("Synthetic demo data loaded. Do NOT report results from it."))
