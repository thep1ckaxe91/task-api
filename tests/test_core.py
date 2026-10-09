import json
from tasks_api.core.errors import PROBLEM_JSON_MIME


def test_health_check(client):
    """Test healthcheck endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"
    assert response.json["service"] == "tasks-api"


def test_openapi_json(client):
    """Test /openapi.json serves raw spec loaded from docs/openapi.yaml."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json
    assert "openapi" in data
    assert data["info"]["title"] == "Tasks API"
    assert "/tasks" in data["paths"]


def test_swagger_ui_docs(client):
    """Test /docs serves Swagger UI HTML."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"SwaggerUIBundle" in response.data
    assert b"/openapi.json" in response.data


def test_rfc7807_404_not_found(client):
    """Test 404 handler formats response according to RFC 7807."""
    response = client.get("/non-existent-route")
    assert response.status_code == 404
    assert response.mimetype == PROBLEM_JSON_MIME
    data = response.json
    assert data["status"] == 404
    assert data["title"] == "Not Found"
    assert "detail" in data
    assert data["instance"] == "/non-existent-route"


def test_rfc7807_405_method_not_allowed(client):
    """Test 405 method not allowed formats response according to RFC 7807."""
    response = client.post("/health", json={})
    assert response.status_code == 405
    assert response.mimetype == PROBLEM_JSON_MIME
    data = response.json
    assert data["status"] == 405
    assert data["title"] == "Method Not Allowed"


def test_jwt_auth_missing_header(client):
    """Test accessing protected route without Authorization header."""
    response = client.get("/tasks")
    assert response.status_code == 401
    assert response.mimetype == PROBLEM_JSON_MIME
    data = response.json
    assert data["status"] == 401
    assert data["title"] == "Unauthorized"
    assert "Missing Authorization header" in data["detail"]


def test_jwt_auth_invalid_token(client):
    """Test accessing protected route with malformed/invalid token."""
    response = client.get("/tasks", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert response.status_code == 401
    assert response.mimetype == PROBLEM_JSON_MIME
    data = response.json
    assert data["status"] == 401
    assert "Invalid token" in data["detail"]


def test_jwt_auth_valid_token_access(client, auth_headers):
    """Test authorized request with valid Bearer JWT."""
    response = client.get("/tasks", headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    assert "data" in data
    assert "limit" in data


def test_create_task_validation_error(client, auth_headers):
    """Test task creation with missing required field returns 422 RFC 7807."""
    response = client.post("/tasks", headers=auth_headers, json={})
    assert response.status_code == 422
    assert response.mimetype == PROBLEM_JSON_MIME
    data = response.json
    assert data["status"] == 422
    assert data["title"] == "Unprocessable Entity"
    assert "invalid_params" in data
    assert any(p["name"] == "title" for p in data["invalid_params"])


def test_task_crud_routing_flow(client, auth_headers):
    """Test full CRUD routing flow with authenticated client."""
    # 1. POST /tasks
    create_res = client.post(
        "/tasks",
        headers=auth_headers,
        json={"title": "Test Architecture Task", "description": "Verify N's deliverables"},
    )
    assert create_res.status_code == 201
    assert "Location" in create_res.headers
    task_id = create_res.json["id"]

    # 2. GET /tasks/<id>
    get_res = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json["id"] == task_id

    # 3. PATCH /tasks/<id>
    patch_res = client.patch(
        f"/tasks/{task_id}",
        headers=auth_headers,
        json={"status": "completed"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json["status"] == "completed"

    # 4. DELETE /tasks/<id>
    del_res = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert del_res.status_code == 204
    assert del_res.data == b""
