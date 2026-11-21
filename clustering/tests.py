import io
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from .models import ClusterRun, County
from .services import ImportErrorList, import_counties_csv, run_clustering


class ImportTests(TestCase):
    def test_rejects_out_of_range_and_reports_all_errors(self):
        csv = "code,name,improved_sanitation_pct\n1,Mombasa,150\n99,Bad,10\n"
        with self.assertRaises(ImportErrorList) as cm:
            import_counties_csv(io.BytesIO(csv.encode()))
        self.assertEqual(len(cm.exception.errors), 2)
        self.assertEqual(County.objects.count(), 0)   # all-or-nothing

    def test_valid_import(self):
        n = import_counties_csv(io.BytesIO(b"code,name,improved_sanitation_pct\n1,Mombasa,88.5\n"))
        self.assertEqual(n, 1)


class PipelineTests(TestCase):
    def setUp(self):
        call_command("seed_demo", verbosity=0)

    def test_kmeans_and_hierarchical(self):
        for algo in ("kmeans", "hierarchical"):
            run = run_clustering(algo, 3)
            self.assertEqual(run.assignments.count(), 47)
            self.assertEqual([p["label"] for p in run.profiles], ["High-need", "Transitional", "Well-served"])
            # ordering invariant: sanitation access rises with cluster index
            means = [p["means"]["improved_sanitation_pct"] for p in run.profiles]
            self.assertEqual(means, sorted(means))

    def test_missing_values_imputed(self):
        County.objects.filter(code__lte=3).update(handwashing_pct=None)
        run = run_clustering("kmeans", 3)
        self.assertEqual(run.k_diagnostics["imputed_cells"], 3)


class ViewTests(TestCase):
    def setUp(self):
        call_command("seed_demo", verbosity=0)

    def test_public_pages_and_login_gate(self):
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(self.client.post(reverse("run"), {"algorithm": "kmeans"}).status_code, 302)
        self.assertEqual(ClusterRun.objects.count(), 0)

    def test_run_detail_and_export(self):
        User.objects.create_user("u", password="pw12345!x")
        self.client.login(username="u", password="pw12345!x")
        r = self.client.post(reverse("run"), {"algorithm": "kmeans", "k": 3}, follow=True)
        self.assertEqual(r.status_code, 200)
        run = ClusterRun.objects.get()
        self.assertEqual(self.client.get(reverse("export_run", args=[run.pk])).status_code, 200)
