from django.contrib import admin
from django.urls import reverse

# Customize the admin dashboard
admin.site.site_url = reverse("home")
admin.site.site_header = "EcoFlux Inventory Administration"

# Register your models here.
