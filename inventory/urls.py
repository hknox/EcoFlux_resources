from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

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
    # Equipment
    path("equipment/", views.EquipmentListView.as_view(), name="view_equipment"),
    path(
        "equipment/add/",
        views.EquipmentCreateView.as_view(),
        name="equipment_add",
    ),
    path(
        "equipment/edit/<int:pk>",
        views.EquipmentUpdateView.as_view(),
        name="equipment_edit",
    ),
    path(
        "equipment/delete/<int:pk>/",
        views.EquipmentDeleteView.as_view(),
        name="equipment_delete",
    ),
    # Fieldnotes
    path("fieldnotes/", views.FieldNoteListView.as_view(), name="view_fieldnotes"),
    path(
        "fieldnotes/add/",
        views.FieldNoteCreateView.as_view(),
        name="fieldnote_add",
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
    path("photos/", views.PhotoListView.as_view(), name="view_photos"),
    path(
        "photos/add/<int:fieldnote>", views.PhotoUploadView.as_view(), name="photo_add"
    ),
    path(
        "photos/edit/<int:pk>",
        views.PhotoUpdateView.as_view(),
        name="photo_edit",
    ),
    path(
        "photos/delete/<int:pk>",
        views.PhotoDeleteView.as_view(),
        name="photo_delete",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
