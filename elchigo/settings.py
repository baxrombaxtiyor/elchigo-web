import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-secret-key')

DEBUG = False

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'elchigo',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'elchigo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'elchigo.wsgi.application'

# Sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
SESSION_FILE_PATH = BASE_DIR / 'sessions'
SESSION_FILE_PATH.mkdir(exist_ok=True)

# Localization
LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

# Static files (ВАЖНО для Render)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Firebase через ENV (ВАЖНО)
FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS')

FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', '')
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY', '')

# Security cookies
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False
SESSION_SAVE_EVERY_REQUEST = True

# Firebase init (исправлено)
import firebase_admin
from firebase_admin import credentials as fb_creds

try:
    firebase_admin.get_app()
except ValueError:
    if FIREBASE_CREDENTIALS:
        cred_dict = json.loads(FIREBASE_CREDENTIALS)
        cred = fb_creds.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)