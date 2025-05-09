# EcorFlux/inventory/urls.py
from django.urls import path

from inventory import views

urlpatterns = [
    path("test", views.test_html, name="testing"),
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
    path("sites/", views.SiteListView.as_view(), name="view_sites"),
    path(
        "sites/edit/<int:pk>/",
        views.SiteUpdateView.as_view(),
        name="edit_site",
    ),
    path(
        "sites/delete/<int:pk>/",
        views.SiteDeleteView.as_view(),
        name="delete_site",
    ),
    path(
        "sites/add/",
        views.SiteCreateView.as_view(),
        name="add_site",
    ),
]
