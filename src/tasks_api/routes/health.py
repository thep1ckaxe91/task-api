from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Liveness & healthcheck endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "tasks-api",
        "version": "1.0.0",
    }), 200
