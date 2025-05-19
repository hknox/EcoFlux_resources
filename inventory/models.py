# Can add 'help_text' to each field creation call, see
# https://docs.djangoproject.com/en/5.2/topics/db/models/, look for
# help_text

from django.db import models
from django.forms import fields


class Site(models.Model):
    description = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    address = models.TextField()
    date_activated = models.DateField()
    date_deactivated = models.DateField(blank=True, null=True)
    gps_coordinates = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.description} ({self.address})"


class InventoryItem(models.Model):
    description = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=50)
    date_purchased = models.DateField()
    notes = models.TextField(blank=True)

    # Using a descriptive related_name, you can write:
    # "some_site.inventory_items.all()"
    # to get all inventory items at that location.
    location = models.ForeignKey(
        Site, on_delete=models.SET_NULL, null=True, related_name="inventory_items"
    )

    def __str__(self):
        return f"{self.description} - {self.serial_number}"


class MaintenanceRecord(models.Model):
    date = models.DateField()
    description = models.TextField()
    item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="maintenance_records"
    )
