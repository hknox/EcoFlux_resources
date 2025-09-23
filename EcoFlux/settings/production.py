"""Django settings specific to the production server on grandwazoo.ddns.net."""

"""Load common settings"""
from .base import *

# Override .base default:
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "grandwazoo.ddns.net",
]

ADMINS = [
    ("Hank", "hank.knox@mcgill.ca"),
]

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME", default="default_name"),
        "USER": config("DB_USER", default="default_user"),
        "PASSWORD": config("DB_PASSWORD", default="default_pass"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="3306"),
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

# Override .base.STATIC_URL = "static/"
STATIC_URL = "/ecoflux/static/"
STATICFILES_DIRS = (BASE_DIR / "static",)
STATIC_ROOT = BASE_DIR / "staticfiles"

# Account Management
# Add this to default account managemeent
LOGIN_URL = "/ecoflux/accounts/login/"

# Photo uploads
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/ecoflux/media/"
# SITE_PHOTO_UPLOAD_SUBDIR = "site_photos/"
# DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
