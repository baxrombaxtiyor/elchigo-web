import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'elchigo',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # ← для статики
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'elchigo.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
        ],
    },
}]

WSGI_APPLICATION = 'elchigo.wsgi.application'

# Сессии — в файл (папка sessions должна существовать)
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
SESSION_FILE_PATH = '/tmp/sessions'
os.makedirs('/tmp/sessions', exist_ok=True)

LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

# Статика — whitenoise
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS', str(BASE_DIR / 'serviceAccountKey.json'))
FIREBASE_PROJECT_ID  = os.getenv('FIREBASE_PROJECT_ID', '')
FIREBASE_API_KEY     = os.getenv('FIREBASE_API_KEY', '')

SESSION_COOKIE_SAMESITE    = 'Lax'
CSRF_COOKIE_SAMESITE       = 'Lax'
CSRF_COOKIE_HTTPONLY       = False
SESSION_SAVE_EVERY_REQUEST = True

import firebase_admin
from firebase_admin import credentials as fb_creds
try:
    firebase_admin.get_app()
except ValueError:
    _cred = fb_creds.Certificate(FIREBASE_CREDENTIALS)
    firebase_admin.initialize_app(_cred)