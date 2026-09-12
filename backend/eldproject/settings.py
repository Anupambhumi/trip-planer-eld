"""Django settings for the TripPilot AI backend."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from backend/.env (if present).
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "dev-insecure-key-change-in-production")
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,.vercel.app,.onrender.com"
).split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "trips",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "eldproject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "eldproject.wsgi.application"

# SQLite is used only for Django's own internal tables (admin, sessions).
# Trip data is stored in MongoDB (see MONGODB_* below) with an ORM fallback.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ---- MongoDB ----
# If MONGODB_URI is set, trips are stored in MongoDB via pymongo.
# If it is empty, the app transparently falls back to the SQLite ORM so it
# still runs with zero setup.
MONGODB_URI = os.environ.get("MONGODB_URI", "")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "eld_trip_planner")
MONGODB_COLLECTION = os.environ.get("MONGODB_COLLECTION", "trips")

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# CORS: allow the React dev server and any deployed frontend.
CORS_ALLOW_ALL_ORIGINS = os.environ.get(
    "CORS_ALLOW_ALL", "True").lower() == "true"
CORS_ALLOWED_ORIGINS = [
    o for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if o
]
CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        "https://*.vercel.app,https://*.onrender.com").split(",") if o
]
