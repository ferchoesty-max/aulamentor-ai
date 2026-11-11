import json
import os
from functools import lru_cache
import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.auth.credentials import AnonymousCredentials

class LocalEmulatorCredentials(credentials.Base):
    def __init__(self, project_id: str):
        self.project_id = project_id

    def get_credential(self):
        return AnonymousCredentials()

    def get_project_id(self):
        return self.project_id

def is_emulator_mode() -> bool:
    auth_host = os.environ.get('FIREBASE_AUTH_EMULATOR_HOST', '').strip()
    db_host = os.environ.get('FIRESTORE_EMULATOR_HOST', '').strip()
    return bool(auth_host and db_host)

@lru_cache(maxsize=1)
def ensure_firebase():
    project_id = os.getenv('FIREBASE_PROJECT_ID', 'aulamentor-ai-demo').strip()
    try:
        app = firebase_admin.get_app()
        return app
    except ValueError:
        pass

    if is_emulator_mode():
        cred = LocalEmulatorCredentials(project_id)
    else:
        raw_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON', '').strip()
        if raw_json:
            data = json.loads(raw_json)
            cred = credentials.Certificate(data)
        else:
            try:
                cred = credentials.ApplicationDefault()
            except Exception:
                cred = LocalEmulatorCredentials(project_id)

    return firebase_admin.initialize_app(cred, {'projectId': project_id})

@lru_cache(maxsize=1)
def get_db():
    ensure_firebase()
    return firestore.client()
