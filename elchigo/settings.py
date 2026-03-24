import firebase_admin
from firebase_admin import credentials as fb_creds
import os, json

try:
    firebase_admin.get_app()
except ValueError:
    cred_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
    if cred_json:
        _cred = fb_creds.Certificate(json.loads(cred_json))
    else:
        _cred = fb_creds.Certificate(str(BASE_DIR / 'serviceAccountKey.json'))
    firebase_admin.initialize_app(_cred)