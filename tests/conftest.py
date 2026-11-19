import sys
from pathlib import Path
import pytest

api_path = Path(__file__).resolve().parent.parent / 'apps' / 'api'
sys.path.insert(0, str(api_path))

from src.http.app import create_app

@pytest.fixture
def app():
    application = create_app(testing=True)
    return application

@pytest.fixture
def client(app):
    return app.test_client()
