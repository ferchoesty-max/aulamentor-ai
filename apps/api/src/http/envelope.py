from flask import jsonify

def ok(data, status: int = 200):
    return jsonify({"success": True, "data": data}), status
