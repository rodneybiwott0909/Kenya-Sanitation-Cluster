from django.contrib import admin
from .models import County, ClusterRun, ClusterAssignment

@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "region", "is_asal", "improved_sanitation_pct", "open_defecation_pct")
    list_filter = ("is_asal", "region")
    search_fields = ("name",)

class AssignmentInline(admin.TabularInline):
    model = ClusterAssignment
    extra = 0

@admin.register(ClusterRun)
class ClusterRunAdmin(admin.ModelAdmin):
    list_display = ("__str__", "silhouette", "davies_bouldin", "created_by")
    inlines = [AssignmentInline]
