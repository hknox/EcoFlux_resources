"""
URL configuration for EcoFlux project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from inventory import views

urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),  # for authentication
    path("admin/", admin.site.urls),  # Django's built-in admin interface
    path("ecoflux/", include("inventory.urls")),
    # TODO: Is this the best way to do this?
    # path("", views.InventoryListView.as_view(), name="root"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    raise ValueError(
        "EcoFlux/urls.py.urlpatterns needs static MEDIA variables for photos"
    )
