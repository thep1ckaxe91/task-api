from flask import Blueprint, g, jsonify, request

from tasks_api.core.auth import require_jwt_auth
from tasks_api.core.errors import ProblemException

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@tasks_bp.route("", methods=["GET"])
@require_jwt_auth
def list_tasks():
    """
    List tasks with cursor pagination.
    To be fully wired by K with Marshmallow pagination schema.
    """
    limit = request.args.get("limit", default=20, type=int)
    cursor = request.args.get("starting_after", default=None, type=str)

    # Stub response unblocking integration and smoke testing
    return jsonify({
        "data": [],
        "has_more": False,
        "next_cursor": None,
        "limit": limit,
    }), 200


@tasks_bp.route("", methods=["POST"])
@require_jwt_auth
def create_task():
    """
    Create a new task.
    To be fully wired by K with TaskCreateSchema and repository insertion.
    """
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        raise ProblemException(
            status=400,
            title="Bad Request",
            detail="Request body must be a valid JSON object.",
        )

    title = payload.get("title")
    if not title:
        raise ProblemException(
            status=422,
            title="Unprocessable Entity",
            detail="Validation failed: 'title' is required.",
            invalid_params=[{"name": "title", "reason": "Field is required and cannot be empty"}],
        )

    task_id = "task-stub-001"
    response_data = {
        "id": task_id,
        "title": title,
        "description": payload.get("description"),
        "status": payload.get("status", "pending"),
        "created_by": g.current_user,
        "created_at": "2026-10-09T10:00:00Z",
        "updated_at": "2026-10-09T10:00:00Z",
    }
    return jsonify(response_data), 201, {"Location": f"/tasks/{task_id}"}


@tasks_bp.route("/<string:task_id>", methods=["GET"])
@require_jwt_auth
def get_task(task_id: str):
    """
    Retrieve task by ID.
    """
    if task_id == "not-found":
        raise ProblemException(
            status=404,
            title="Not Found",
            detail=f"Task with id '{task_id}' was not found.",
        )

    return jsonify({
        "id": task_id,
        "title": "Stub Task Title",
        "description": "Stub Task Description",
        "status": "pending",
        "created_by": g.current_user,
        "created_at": "2026-10-09T10:00:00Z",
        "updated_at": "2026-10-09T10:00:00Z",
    }), 200


@tasks_bp.route("/<string:task_id>", methods=["PATCH"])
@require_jwt_auth
def update_task(task_id: str):
    """
    Update task using RFC 7396 JSON Merge Patch semantics.
    """
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        raise ProblemException(
            status=400,
            title="Bad Request",
            detail="Request body must be a valid JSON object.",
        )

    if task_id == "not-found":
        raise ProblemException(
            status=404,
            title="Not Found",
            detail=f"Task with id '{task_id}' was not found.",
        )

    return jsonify({
        "id": task_id,
        "title": payload.get("title", "Updated Task"),
        "description": payload.get("description", "Updated Description"),
        "status": payload.get("status", "in_progress"),
        "created_by": g.current_user,
        "created_at": "2026-10-09T10:00:00Z",
        "updated_at": "2026-10-09T10:30:00Z",
    }), 200


@tasks_bp.route("/<string:task_id>", methods=["DELETE"])
@require_jwt_auth
def delete_task(task_id: str):
    """
    Delete task by ID. Returns 204 No Content on success.
    """
    if task_id == "not-found":
        raise ProblemException(
            status=404,
            title="Not Found",
            detail=f"Task with id '{task_id}' was not found.",
        )

    return "", 204
