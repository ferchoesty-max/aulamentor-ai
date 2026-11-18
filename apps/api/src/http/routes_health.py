from datetime import datetime, timezone
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
@health_bp.route('/api/v1/health', methods=['GET'])
def get_health():
    return jsonify({
        'status': 'ok',
        'service': 'aulamentor-api',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0'
    }), 200
