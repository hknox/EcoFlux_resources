# Can add 'help_text' to each field creation call, see
# https://docs.djangoproject.com/en/5.2/topics/db/models/, look for
# help_text
import os
import uuid

from django.db import models
from django.conf import settings
from django.utils.timezone import now


class Site(models.Model):
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


class InventoryItem(models.Model):
    instrument = models.CharField(max_length=75)
    manufacturer = models.CharField(max_length=75, blank=True)
    model_number = models.CharField(max_length=75, blank=True)
    serial_number = models.CharField(max_length=50, blank=True)
    date_purchased = models.DateField()
    notes = models.TextField(blank=True)
    location = models.ForeignKey(
        Site, on_delete=models.SET_NULL, null=True, blank=True, related_name="inventory"
    )

    def __str__(self):
        return f"{self.instrument} - {self.serial_number}"


class FieldNote(models.Model):
    site = models.ForeignKey(Site, related_name="fieldnotes", on_delete=models.CASCADE)
    note = models.TextField()
    date_submitted = models.DateField(default=now)
    summary = models.CharField(max_length=80, blank=True)
    submitter = models.CharField()


def site_photo_upload_path(instance, filename):
    ext = filename.split(".")[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join(settings.SITE_PHOTO_UPLOAD_SUBDIR, new_filename)


class Photo(models.Model):
    image = models.ImageField(upload_to=site_photo_upload_path)
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateField(default=now)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="photos")
