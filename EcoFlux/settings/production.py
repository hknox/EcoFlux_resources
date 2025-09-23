"""Django settings specific to the production server on grandwazoo.ddns.net."""

"""Load common settings"""
from .base import *

# Override .base default:
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "grandwazoo.ddns.net",
]

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME", "default_name"),
        "USER": os.environ.get("DB_USER", "default_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "default_pass"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "3306"),
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

# Override .base.STATIC_URL = "static/"
STATIC_URL = "/ecoflux/static/"
STATICFILES_DIRS = (BASE_DIR / "static",)
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Account Management
# Add this to default account managemeent
LOGIN_URL = "/ecoflux/accounts/login/"


# Photo uploads
MEDIA_URL = "/ecoflux/media/"
MEDIA_ROOT = BASE_DIR / "media"
# SITE_PHOTO_UPLOAD_SUBDIR = "site_photos/"
