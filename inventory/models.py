# Can add 'help_text' to each field, see
# https://docs.djangoproject.com/en/5.1/topics/db/models/, look for
# help_text

from django.db import models


class Location(models.Model):
    description = models.CharField(max_length=100)
    address = models.TextField()
    gps_coordinates = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.description} ({self.address})"


class InventoryItem(models.Model):
    description = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=50)
    date_purchased = models.DateField()
    notes = models.TextField(blank=True, help_text="Free-form notes for this item.")
    # Using a descriptive related_name, you can write:
    # "a_location.inventory_items.all()"
    # to get all inventory items at that location.
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, related_name="inventory_items"
    )

    class Meta:
        ordering = [
            "id",
        ]

    def __str__(self):
        return f"{self.description} - {self.serial_number}"


class MaintenanceRecord(models.Model):
    date = models.DateField()
    description = models.TextField()
    item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="maintenance_records"
    )
