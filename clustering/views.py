import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import charts
from .forms import RunForm, UploadForm
from .models import INDICATORS, ClusterRun, County
from .services import ImportErrorList, import_counties_csv, run_clustering


def dashboard(request):
    latest = ClusterRun.objects.first()
    return render(request, "clustering/dashboard.html", {
        "county_count": County.objects.count(),
        "with_data": County.objects.exclude(improved_sanitation_pct__isnull=True).count(),
        "latest": latest, "runs": ClusterRun.objects.all()[:5], "run_form": RunForm()})


def county_list(request):
    return render(request, "clustering/counties.html", {
        "counties": County.objects.all(), "indicators": INDICATORS})


@login_required
def upload(request):
    form = UploadForm(request.POST or None, request.FILES or None)
    errors = []
    if request.method == "POST" and form.is_valid():
        try:
            n = import_counties_csv(form.cleaned_data["file"])
            messages.success(request, f"Imported {n} counties.")
            return redirect("counties")
        except ImportErrorList as e:
            errors = e.errors
    return render(request, "clustering/upload.html", {"form": form, "errors": errors})


@login_required
@require_POST
def run_view(request):
    form = RunForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid clustering options.")
        return redirect("dashboard")
    try:
        run = run_clustering(form.cleaned_data["algorithm"], form.cleaned_data["k"], request.user)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("dashboard")
    return redirect("run_detail", pk=run.pk)


def run_list(request):
    return render(request, "clustering/runs.html", {"runs": ClusterRun.objects.all()})


def run_detail(request, pk):
    run = get_object_or_404(ClusterRun, pk=pk)
    return render(request, "clustering/run_detail.html", {
        "run": run, "indicators": dict((f, l) for f, l, _ in INDICATORS),
        "pca_json": charts.pca_scatter(run), "k_json": charts.k_selection(run),
        "heat_json": charts.profile_heatmap(run), "map_json": charts.choropleth(run)})


def export_run(request, pk):
    run = get_object_or_404(ClusterRun, pk=pk)
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = f'attachment; filename="clusters_run_{run.pk}.csv"'
    w = csv.writer(resp)
    w.writerow(["county_code", "county", "cluster", "label", "pc1", "pc2"])
    for a in run.assignments.select_related("county"):
        w.writerow([a.county.code, a.county.name, a.cluster, a.label, round(a.pc1, 4), round(a.pc2, 4)])
    return resp
