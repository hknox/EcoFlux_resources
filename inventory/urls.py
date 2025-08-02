# EcorFlux/inventory/urls.py
from django.urls import path

from inventory import views

urlpatterns = [
    path("", views.SiteListView.as_view(), name="home"),
    # Sites
    path("sites/", views.SiteListView.as_view(), name="view_sites"),
    path(
        "sites/add/",
        views.SiteCreateView.as_view(),
        name="site_add",
    ),
    path(
        "sites/edit/<int:pk>/",
        views.SiteUpdateView.as_view(),
        name="site_edit",
    ),
    path(
        "sites/delete/<int:pk>/",
        views.SiteDeleteView.as_view(),
        name="site_delete",
    ),
    # Inventory items
    path("inventory/", views.InventoryListView.as_view(), name="view_inventory"),
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
    # Fieldnotes
    path("fieldnotes/", views.FieldNoteListView.as_view(), name="view_fieldnotes"),
    path(
        "fieldnotes/create/",
        views.FieldNoteCreateView.as_view(),
        name="fieldnote_create",
    ),
    path(
        "fieldnotes/edit/<int:pk>",
        views.FieldNoteUpdateView.as_view(),
        name="fieldnote_edit",
    ),
    path(
        "fieldnotes/delete/<int:pk>/",
        views.FieldNoteDeleteView.as_view(),
        name="fieldnote_delete",
    ),
    # Photos
    path("photos/", views.EndOfInternet, name="photos"),
    path("photos/add", views.upload_photo, name="new_photo"),
]
