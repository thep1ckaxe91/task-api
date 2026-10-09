import os
from flask import Flask, jsonify, make_response
import yaml

app = Flask(__name__)

OPENAPI_SPEC_PATH = os.path.join(os.path.dirname(__file__), 'openapi.yaml')

# In-memory storage (reserved for K to implement)
tasks = {}

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
# CRUD Endpoints (Stubs for K to implement)
# ==========================================

@app.route('/tasks', methods=['GET'])
def list_tasks():
    return jsonify({'message': 'Endpoint not implemented yet'}), 501

@app.route('/tasks', methods=['POST'])
def create_task():
    return jsonify({'message': 'Endpoint not implemented yet'}), 501

@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    return jsonify({'message': 'Endpoint not implemented yet'}), 501

@app.route('/tasks/<int:task_id>', methods=['PATCH'])
def update_task(task_id):
    return jsonify({'message': 'Endpoint not implemented yet'}), 501

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    return jsonify({'message': 'Endpoint not implemented yet'}), 501

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
