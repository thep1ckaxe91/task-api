import os
import yaml
from flask import Flask, Response, jsonify, make_response, request, url_for
from itertools import count

app = Flask(__name__)

tasks: dict[int, dict] = {}
_id_seq = count(1)

OPENAPI_SPEC_PATH = os.path.join(os.path.dirname(__file__), 'openapi.yaml')
ALLOWED_FIELDS = frozenset({"title", "description", "completed"})

@app.route('/openapi.json', methods=['GET'])
def get_openapi_spec():
    if not os.path.exists(OPENAPI_SPEC_PATH):
        return jsonify({'error': 'openapi.yaml not found'}), 404
    with open(OPENAPI_SPEC_PATH, 'r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)
    return jsonify(spec)

@app.route('/docs', methods=['GET'])
def docs():
    swagger_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Tasks API - Swagger UI</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js" crossorigin="anonymous"></script>
<script>
  window.onload = () => {
    SwaggerUIBundle({
      url: '/openapi.json',
      dom_id: '#swagger-ui',
    });
  };
</script>
</body>
</html>"""
    return make_response(swagger_html)

# ==========================================
# CRUD Endpoints
# ==========================================

def error(message: str, status: int):
    return jsonify(error=message), status


def parse_json_obj():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None, error("request body must be a JSON object", 400)
    return body, None


def validate_fields(body: dict) -> str | None:
    unknown = set(body) - ALLOWED_FIELDS
    if unknown:
        return f"unknown field(s): {', '.join(sorted(unknown))}"

    if "title" in body:
        title = body["title"]
        if not isinstance(title, str) or not title.strip():
            return "title must be a non-empty string"
    if "description" in body and not isinstance(body["description"], str):
        return "description must be a string"
    if "completed" in body and not isinstance(body["completed"], bool):
        return "completed must be a boolean"

    return None


@app.route('/tasks', methods=['GET'])
def list_tasks():
    return jsonify([dict(t) for t in tasks.values()]), 200


@app.route('/tasks', methods=['POST'])
def create_task():
    body, err = parse_json_obj()
    if err:
        return err
    assert(isinstance(body, dict))
    if "title" not in body:
        return error("title is required", 400)
    msg = validate_fields(body)
    if msg:
        return error(msg, 400)

    task_id = next(_id_seq)
    task = {
        "id": task_id,
        "title": body["title"],
        "description": body.get("description", ""),
        "completed": body.get("completed", False)
    }
    tasks[task_id] = task
    snapshot = dict(task)

    resp = jsonify(snapshot)
    resp.status_code = 201
    resp.headers["Location"] = url_for("get_task", task_id=task_id)
    return resp


@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = tasks.get(task_id)
    snapshot = dict(task) if task is not None else None
    if snapshot is None:
        return error("task not found", 404)
    return jsonify(snapshot), 200


@app.route('/tasks/<int:task_id>', methods=['PATCH'])
def update_task(task_id):
    return jsonify({'message': 'Endpoint not implemented yet'}), 501

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    removed = tasks.pop(task_id, None)
    if removed is None:
        return error("task not found", 404)
    return Response("", status=204)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
