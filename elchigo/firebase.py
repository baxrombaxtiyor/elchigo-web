# elchigo/firebase.py
import firebase_admin
from firebase_admin import credentials, firestore, auth
from django.conf import settings


def _init():
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
        firebase_admin.initialize_app(cred)


def get_db():
    _init()
    return firestore.client()


def get_auth():
    _init()
    return auth