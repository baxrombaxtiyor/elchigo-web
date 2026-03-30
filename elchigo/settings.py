import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-elchigo-change-in-production')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']
PRINT_AGENT_URL = 'https://unshunnable-blossomy-fransisca.ngrok-free.dev'  # IP твоего компьютера
INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'elchigo',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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

# Сессии
SESSION_ENGINE   = 'django.contrib.sessions.backends.file'
SESSION_FILE_PATH = '/tmp/elchigo_sessions'
os.makedirs(SESSION_FILE_PATH, exist_ok=True)

LANGUAGE_CODE = 'ru'
TIME_ZONE     = 'Asia/Tashkent'
USE_I18N      = True
USE_TZ        = False

# Статика
STATIC_URL    = '/static/'
STATIC_ROOT   = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Firebase публичные ключи
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', '')
FIREBASE_API_KEY    = os.getenv('FIREBASE_API_KEY', '')

# CSRF и сессии
SESSION_COOKIE_SAMESITE    = 'Lax'
CSRF_COOKIE_SAMESITE       = 'Lax'
CSRF_COOKIE_HTTPONLY       = False
SESSION_SAVE_EVERY_REQUEST = True
CSRF_TRUSTED_ORIGINS       = [
    'https://*.railway.app',
    'https://*.up.railway.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Firebase Admin инициализация
import firebase_admin
from firebase_admin import credentials as fb_creds

try:
    firebase_admin.get_app()
except ValueError:
    cred_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
    if cred_json:
        _cred = fb_creds.Certificate(json.loads(cred_json))
    else:
        _cred = fb_creds.Certificate(str(BASE_DIR / 'serviceAccountKey.json'))
    firebase_admin.initialize_app(_cred)