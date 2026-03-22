# elchigo/firebase.py
from firebase_admin import firestore, auth

def get_db():
    return firestore.client()

def get_auth():
    return auth