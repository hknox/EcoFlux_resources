# EcorFlux/inventory/urls.py
from django.urls import path

from inventory import views

urlpatterns = [
    path("", views.home, name="home"),
]
