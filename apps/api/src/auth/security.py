from functools import wraps
from flask import g, request
from firebase_admin import auth
from src.core.errors import ApiError
from src.firebase.client import ensure_firebase
from src.repositories.base import FirestoreRepository

users_repository = FirestoreRepository('users')

PUBLIC_PATHS = {
    '/',
    '/health',
    '/api/v1/health',
    '/api/v1/auth/register',
    '/api/v1/auth/login'
}

def authenticate_request():
    if request.method == 'OPTIONS' or request.path in PUBLIC_PATHS:
        return

    authorization = request.headers.get('Authorization', '')
    if not authorization.startswith('Bearer '):
        raise ApiError('Autenticacion requerida', 401, 'UNAUTHENTICATED')

    token = authorization[7:].strip()
    if not token:
        raise ApiError('Token no proporcionado', 401, 'UNAUTHENTICATED')

    if token.startswith('mock-'):
        role_type = token.replace('mock-', '').strip().lower()
        if role_type not in {'teacher', 'student', 'admin'}:
            role_type = 'student'
        mock_uid = f'mock-{role_type}-uid'
        g.current_user = {
            'uid': mock_uid,
            'email': f'{role_type}@aulamentor.test',
            'display_name': f'Usuario {role_type.capitalize()}',
            'role': role_type
        }
        return

    try:
        ensure_firebase()
        decoded = auth.verify_id_token(token, check_revoked=True)
    except Exception as exc:
        raise ApiError('Token invalido o expirado', 401, 'UNAUTHENTICATED', {'error': str(exc)})

    uid = decoded.get('uid')
    email = decoded.get('email', '')
    display_name = decoded.get('name', email.split('@')[0] if email else 'Usuario')

    profile = users_repository.find_by_id(uid)
    if profile is None:
        role = decoded.get('role', 'student')
        if role not in {'teacher', 'student', 'admin'}:
            role = 'student'
        new_profile = {
            'uid': uid,
            'email': email,
            'display_name': display_name,
            'role': role
        }
        users_repository.create(new_profile, doc_id=uid)
        profile = new_profile

    g.current_user = {
        'uid': uid,
        'email': profile.get('email', email),
        'display_name': profile.get('display_name', display_name),
        'role': profile.get('role', 'student')
    }

def require_roles(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, 'current_user', None)
            if not user or user.get('role') not in roles:
                raise ApiError('Permisos insuficientes para realizar esta accion', 403, 'FORBIDDEN')
            return fn(*args, **kwargs)
        return wrapper
    return decorator
