import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-secret-key')

DEBUG = False

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
]

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

# ── Сессии ────────────────────────────────────────────────────────────────────
# Вместо файловых сессий используем куки
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

SESSION_COOKIE_SAMESITE    = 'Lax'
CSRF_COOKIE_SAMESITE       = 'Lax'
CSRF_COOKIE_HTTPONLY       = False
SESSION_SAVE_EVERY_REQUEST = True

# ── Локализация ───────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'ru'
TIME_ZONE     = 'Asia/Tashkent'
USE_I18N      = True
USE_TZ        = True

# ── Статика ───────────────────────────────────────────────────────────────────
STATIC_URL   = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT  = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── Firebase публичные ключи ──────────────────────────────────────────────────
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', '')
FIREBASE_API_KEY    = os.getenv('FIREBASE_API_KEY', '')

# ── Firebase Admin SDK ────────────────────────────────────────────────────────
import firebase_admin
from firebase_admin import credentials as fb_creds

# Читаем из FIREBASE_CREDENTIALS_JSON или FIREBASE_CREDENTIALS
FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS_JSON', '') or \
                       os.getenv('FIREBASE_CREDENTIALS', '')

try:
    firebase_admin.get_app()
except ValueError:
    if FIREBASE_CREDENTIALS:
        try:
            cred_dict = json.loads(FIREBASE_CREDENTIALS)
            cred = fb_creds.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print('✅ Firebase initialized successfully')
        except Exception as e:
            print(f'❌ Firebase init error: {e}')
    else:
        # Локально — используем файл
        cred_file = BASE_DIR / 'serviceAccountKey.json'
        if cred_file.exists():
            cred = fb_creds.Certificate(str(cred_file))
            firebase_admin.initialize_app(cred)
            print('✅ Firebase initialized from file')
        else:
            print('❌ Firebase credentials not found!')