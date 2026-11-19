from flask import jsonify

class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = 'BAD_REQUEST', details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}

    def to_dict(self):
        result = {
            'success': False,
            'error': {
                'code': self.code,
                'message': self.message
            }
        }
        if self.details:
            result['error']['details'] = self.details
        return result

def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return jsonify(err.to_dict()), err.status_code

    @app.errorhandler(404)
    def handle_not_found(err):
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Recurso no encontrado'
            }
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(err):
        return jsonify({
            'success': False,
            'error': {
                'code': 'METHOD_NOT_ALLOWED',
                'message': 'Metodo no permitido'
            }
        }), 405

    @app.errorhandler(500)
    def handle_server_error(err):
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Error interno del servidor'
            }
        }), 500
