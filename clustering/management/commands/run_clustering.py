from django.core.management.base import BaseCommand
from clustering.services import run_clustering


class Command(BaseCommand):
    help = "Run K-Means or Hierarchical clustering from the command line."

    def add_arguments(self, parser):
        parser.add_argument("--algorithm", choices=["kmeans", "hierarchical"], default="kmeans")
        parser.add_argument("--k", type=int, default=None)

    def handle(self, *a, **o):
        run = run_clustering(o["algorithm"], o["k"])
        self.stdout.write(f"{run} silhouette={run.silhouette:.3f}")
        for p in run.profiles:
            self.stdout.write(f"  {p['label']} ({p['n']}): {', '.join(p['counties'])}")
