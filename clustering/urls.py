from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("counties/", views.county_list, name="counties"),
    path("upload/", views.upload, name="upload"),
    path("run/", views.run_view, name="run"),
    path("runs/", views.run_list, name="runs"),
    path("runs/<int:pk>/", views.run_detail, name="run_detail"),
    path("runs/<int:pk>/export/", views.export_run, name="export_run"),
]
