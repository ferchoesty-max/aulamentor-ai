from flask import Blueprint, g, jsonify, request
from src.core.errors import ApiError
from src.repositories.base import FirestoreRepository

auth_bp = Blueprint('auth', __name__)
users_repo = FirestoreRepository('users')

@auth_bp.route('/api/v1/auth/me', methods=['GET'])
def get_current_user():
    user = getattr(g, 'current_user', None)
    if not user:
        raise ApiError('No autenticado', 401, 'UNAUTHENTICATED')
    return jsonify({
        'success': True,
        'data': user
    }), 200

@auth_bp.route('/api/v1/auth/role', methods=['PUT'])
def update_user_role():
    user = getattr(g, 'current_user', None)
    if not user:
        raise ApiError('No autenticado', 401, 'UNAUTHENTICATED')

    payload = request.get_json(silent=True) or {}
    new_role = payload.get('role', '').strip().lower()
    if new_role not in {'teacher', 'student', 'admin'}:
        raise ApiError('Rol no valido. Permitidos: teacher, student, admin', 422, 'VALIDATION_ERROR')

    target_uid = payload.get('uid', user['uid'])
    if target_uid != user['uid'] and user.get('role') != 'admin':
        raise ApiError('Solo administradores pueden cambiar roles de otros usuarios', 403, 'FORBIDDEN')

    updated = users_repo.update(target_uid, {'role': new_role})
    return jsonify({
        'success': True,
        'data': updated
    }), 200
