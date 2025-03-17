# EcorFlux/inventory/urls.py
from django.urls import path

from inventory import views

urlpatterns = [
    path("", views.home, name="home"),
    path("locations/", views.LocationListView.as_view(), name="view_locations"),
    path(
        "locations/edit/<int:pk>/",
        views.LocationUpdateView.as_view(),
        name="edit_location",
    ),
    path(
        "locations/add/",
        views.LocationCreateView.as_view(),
        name="add_location",
    ),
    path(
        "locations/delete/<int:pk>/",
        views.LocationDeleteView.as_view(),
        name="delete_location",
    ),
]
