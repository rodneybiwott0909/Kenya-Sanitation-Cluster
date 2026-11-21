from django.db import models

INDICATORS = [
    ("improved_sanitation_pct", "Improved sanitation (%)", True),   # (field, label, higher_is_better)
    ("open_defecation_pct", "Open defecation (%)", False),
    ("improved_water_pct", "Improved water source (%)", True),
    ("handwashing_pct", "Handwashing facility (%)", True),
    ("poverty_rate_pct", "Poverty rate (%)", False),
    ("urban_pop_pct", "Urban population (%)", True),
]
INDICATOR_FIELDS = [f for f, _, _ in INDICATORS]


class County(models.Model):
    code = models.PositiveSmallIntegerField(unique=True)
    name = models.CharField(max_length=60, unique=True)
    region = models.CharField(max_length=60, blank=True)
    is_asal = models.BooleanField(default=False, verbose_name="ASAL county")
    improved_sanitation_pct = models.FloatField(null=True, blank=True)
    open_defecation_pct = models.FloatField(null=True, blank=True)
    improved_water_pct = models.FloatField(null=True, blank=True)
    handwashing_pct = models.FloatField(null=True, blank=True)
    poverty_rate_pct = models.FloatField(null=True, blank=True)
    urban_pop_pct = models.FloatField(null=True, blank=True)
    source = models.CharField(max_length=120, blank=True, help_text="e.g. KDHS 2022, KNBS 2019")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        verbose_name_plural = "counties"

    def __str__(self):
        return self.name


class ClusterRun(models.Model):
    ALGORITHMS = [("kmeans", "K-Means"), ("hierarchical", "Hierarchical (Ward)")]
    algorithm = models.CharField(max_length=20, choices=ALGORITHMS)
    n_clusters = models.PositiveSmallIntegerField()
    silhouette = models.FloatField(null=True)
    davies_bouldin = models.FloatField(null=True)
    explained_variance = models.JSONField(default=list)       # PCA ratios
    k_diagnostics = models.JSONField(default=dict)            # {"k": [...], "inertia": [...], "silhouette": [...]}
    profiles = models.JSONField(default=list)                 # per-cluster mean indicators
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey("auth.User", null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_algorithm_display()} k={self.n_clusters} ({self.created_at:%Y-%m-%d %H:%M})"


class ClusterAssignment(models.Model):
    run = models.ForeignKey(ClusterRun, related_name="assignments", on_delete=models.CASCADE)
    county = models.ForeignKey(County, on_delete=models.CASCADE)
    cluster = models.PositiveSmallIntegerField()
    label = models.CharField(max_length=60)
    pc1 = models.FloatField()
    pc2 = models.FloatField()

    class Meta:
        unique_together = ("run", "county")
        ordering = ["cluster", "county__name"]
