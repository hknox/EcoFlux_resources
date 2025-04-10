# EcorFlux/inventory/urls.py
from django.urls import path

from inventory import views

urlpatterns = [
    path("", views.InventoryListView.as_view(), name="home"),
    path(
        "inventory/add/",
        views.InventoryItemCreateView.as_view(),
        name="inventory_add",
    ),
    path(
        "inventory/edit/<int:pk>",
        views.InventoryItemUpdateView.as_view(),
        name="inventory_edit",
    ),
    path("locations/", views.LocationListView.as_view(), name="view_locations"),
    path(
        "locations/edit/<int:pk>/",
        views.LocationUpdateView.as_view(),
        name="edit_location",
    ),
    path(
        "locations/delete/<int:pk>/",
        views.LocationDeleteView.as_view(),
        name="delete_location",
    ),
    path(
        "locations/add/",
        views.LocationCreateView.as_view(),
        name="add_location",
    ),
]
