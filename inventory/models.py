from django.db import models


class Location(models.Model):
    description = models.CharField(max_length=100)
    address = models.TextField()
    gps_coordinates = models.CharField(max_length=50)

    # def __str__(self):
    #     return self.description[:10]


class Inventory(models.Model):
    description = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    date_purchased = models.DateField()
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)


class Maintenance_Record(models.Model):
    date = models.DateField()
    description = models.TextField()
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE)
