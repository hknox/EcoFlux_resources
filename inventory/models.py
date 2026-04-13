# Can add 'help_text' to each field creation call, see
# https://docs.djangoproject.com/en/5.2/topics/db/models/, look for
# help_text
import os

from django.db import models
from django.utils.timezone import now
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from inventory.media_processing.media_paths import (
    site_photo_upload_path,
    document_upload_path,
    document_thumbnail_upload_path,
    image_thumbnail_upload_path,
)
from inventory.media_processing.thumbnails import (

class GetDocumentMixin:
    """Mixin providing helper class for objects that can be related to
    Documents.

    It provides 2 equivalent ways to get related documents."""

    def get_documents(self):
        """Return all documents associated with an object of this class."""

        return Document.objects.filter(
            content_type=ContentType.objects.get_for_model(self.__class__),
            object_id=self.id,
        )

    @property
    def documents(self):

        return self.get_documents()


class Site(models.Model, GetDocumentMixin):
    name = models.CharField(max_length=50)  # , help_text="Site name")
    code = models.CharField(max_length=10)  # , help_text="Short code for internal use")
    amp = models.CharField(
        max_length=10
    )  # , help_text="AmeriFlux Management Project code")
    location = models.CharField(max_length=250)
    description = models.TextField()  # help_text="Full site description")
    date_activated = models.DateField()
    date_retired = models.DateField(blank=True, null=True)
    gps_coordinates = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.code}: {self.name}"


class DOI(models.Model):
    """Class for a Data Object Identifier to a Site"""

    label = models.CharField(max_length=20)
    doi_link = models.URLField()
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="doi_records")


class Equipment(models.Model, GetDocumentMixin):
    instrument = models.CharField(max_length=75)
    manufacturer = models.CharField(max_length=75, blank=True)
    model_number = models.CharField(max_length=75, blank=True)
    serial_number = models.CharField(max_length=50, blank=True)
    date_purchased = models.DateField()
    notes = models.TextField(blank=True)
    site = models.ForeignKey(
        Site, on_delete=models.SET_NULL, null=True, blank=True, related_name="equipment"
    )

    def __str__(self):
        return f"{self.instrument} - {self.serial_number}"


class History(models.Model):
    date = models.DateField(default=now)
    note = models.TextField()
    item = models.ForeignKey(
        Equipment, related_name="history", on_delete=models.CASCADE
    )


class FieldNote(models.Model, GetDocumentMixin):
    site = models.ForeignKey(Site, related_name="fieldnotes", on_delete=models.CASCADE)
    note = models.TextField()
    date_visited = models.DateField(default=now)
    summary = models.CharField(max_length=80, blank=True)
    submitter = models.CharField(max_length=50, blank=True)
    site_visitors = models.CharField(max_length=250, blank=True, default="")


class Photo(models.Model):
    photo = models.ImageField(upload_to=site_photo_upload_path)
    photo = models.ImageField(upload_to=site_photo_upload_path, blank=False, null=False)
    date_taken = models.DateField(blank=True, null=True)
    taken_by = models.CharField(max_length=100, blank=True)
    fieldnote = models.ForeignKey(
        FieldNote, on_delete=models.CASCADE, related_name="photos"
    )


class Document(models.Model):
    # Generic relation fields
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    # Important: GenericForeignKey is not a database field! Only
    # content_type and object_id are actual database columns.
    content_object = GenericForeignKey("content_type", "object_id")

    date_uploaded = models.DateField(default=now)
    submitter = models.CharField(max_length=50, blank=True, null=True)
    date_received = models.DateField()
    summary = models.CharField(max_length=80)
    file = models.FileField(
        verbose_name="document",
        upload_to=document_upload_path,
        blank=False,
        null=False,
    )

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
