# EcorFlux/inventory/urls.py
from django.urls import path

from inventory import views

urlpatterns = [
    path("", views.home, name="home"),
    path("locations/", views.LocationListView.as_view(), name="view_locations"),
    path(
        "locations/edit/<int:pk>/",
        views.LocationDetailView.as_view(),
        name="edit_location",
    ),
]
