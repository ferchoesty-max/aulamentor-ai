import pytest
from flask import g
from src.auth.security import require_roles
from src.core.errors import ApiError

def test_health_endpoint(client):
    res = client.get('/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'ok'
    assert data['service'] == 'aulamentor-api'

def test_api_v1_health_endpoint(client):
    res = client.get('/api/v1/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'ok'

def test_unauthenticated_request(client):
    res = client.get('/api/v1/auth/me')
    assert res.status_code == 401
    data = res.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'UNAUTHENTICATED'

def test_authenticated_with_mock_student(client):
    res = client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer mock-student'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['role'] == 'student'

def test_authenticated_with_mock_teacher(client):
    res = client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer mock-teacher'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['role'] == 'teacher'

def test_require_roles_decorator(app):
    @require_roles('teacher', 'admin')
    def teacher_action():
        return 'success'

    with app.test_request_context():
        g.current_user = {'uid': '123', 'role': 'student'}
        with pytest.raises(ApiError) as exc_info:
            teacher_action()
        assert exc_info.value.status_code == 403
        assert exc_info.value.code == 'FORBIDDEN'

        g.current_user = {'uid': '456', 'role': 'teacher'}
        assert teacher_action() == 'success'
