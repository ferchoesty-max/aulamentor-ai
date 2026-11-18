def test_health_check_smoke(client):
    res = client.get('/api/v1/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'ok'
    assert data['service'] == 'aulamentor-api'

def test_auth_unauthorized_smoke(client):
    res = client.get('/api/v1/auth/me')
    assert res.status_code == 401
    data = res.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'UNAUTHENTICATED'

def test_auth_student_smoke(client):
    res = client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer mock-student'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['role'] == 'student'
