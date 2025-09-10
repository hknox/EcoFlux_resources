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


class Equipment(models.Model):
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


class FieldNote(models.Model):
    site = models.ForeignKey(Site, related_name="fieldnotes", on_delete=models.CASCADE)
    note = models.TextField()
    date_visited = models.DateField(default=now)
    summary = models.CharField(max_length=80, blank=True)
    submitter = models.CharField(max_length=50, blank=True)
    site_visitors = models.CharField(max_length=250, blank=True, default="")


def site_photo_upload_path(instance, filename):
    # Get the extension
    ext = filename.split(".")[-1].lower()
    # Generate a unique filename
    unique_name = f"{uuid.uuid4()}.{ext}"
    # Organize by site ID
    path = os.path.join("site_photos", f"site_{instance.site_id}", unique_name)
    print(f"upload to {path}")
    return os.path.join("site_photos", f"site_{instance.site_id}", unique_name)


class Photo(models.Model):
    photo = models.ImageField(upload_to=site_photo_upload_path)
    date_taken = models.DateField(blank=True, null=True)
    taken_by = models.CharField(max_length=100, blank=True)
    fieldnote = models.ForeignKey(
        FieldNote, on_delete=models.CASCADE, related_name="photos"
    )

    # # OR:
    # @property
    # def date_taken(self):
    #     return self.fieldnote.date


# class Document(models.Model):
#     date_uploaded = models.DateField(default=now)
#     submitter = models.CharField(max_length=50, blank=True)
#     file = models.FileField(
#         verbose_name="equipment_document", name="document", upload_to=""
#     )
