# EcorFlux/inventory/urls.py
from django.urls import path

from inventory import views

urlpatterns = [
    path("test/", views.test_html, name="testing"),
    # temporary home view? or change back to InventoryListView?
    path("", views.SiteListView.as_view(), name="home"),
    path("sites/", views.SiteListView.as_view(), name="view_sites"),
    path("fieldnotes/", views.FieldNoteListView.as_view(), name="view_fieldnotes"),
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
        "fieldnotes/delete/<int:pk>/",
        views.FieldNoteDeleteView.as_view(),
        name="fieldnote_delete",
    ),
    path(
        "sites/add/",
        views.SiteCreateView.as_view(),
        name="add_site",
    ),
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
    path("photos/", views.EndOfInternet, name="photos"),
    path("photos/add", views.upload_photo, name="new_photo"),
]
