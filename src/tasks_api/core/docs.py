from pathlib import Path
from flask import Blueprint, current_app, jsonify, render_template_string
import yaml

from tasks_api.core.errors import ProblemException

docs_bp = Blueprint("docs", __name__)


SWAGGER_UI_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>tasks-api - Swagger UI</title>
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" />
  <link rel="icon" type="image/png" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/favicon-32x32.png" sizes="32x32" />
  <style>
    html {
      box-sizing: border-box;
      overflow: -moz-scrollbars-vertical;
      overflow-y: scroll;
    }
    *, *:before, *:after {
      box-sizing: inherit;
    }
    body {
      margin: 0;
      background: #fafafa;
    }
    .topbar {
      display: none;
    }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = function() {
      window.ui = SwaggerUIBundle({
        url: "{{ spec_url }}",
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        layout: "StandaloneLayout",
        persistAuthorization: true,
        displayRequestDuration: true
      });
    };
  </script>
</body>
</html>
"""


@docs_bp.route("/openapi.json", methods=["GET"])
def get_openapi_spec():
    """
    Serve raw OpenAPI specification as JSON directly loaded from openapi.yaml.
    Guarantees 100% parity with zero dynamic drift.
    """
    yaml_path = Path(current_app.config.get("OPENAPI_YAML_PATH"))
    if not yaml_path.is_file():
        raise ProblemException(
            status=500,
            title="OpenAPI Spec Not Found",
            detail=f"OpenAPI definition file not found at path: {yaml_path}",
        )

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            spec_data = yaml.safe_load(f)
    except Exception as exc:
        raise ProblemException(
            status=500,
            title="OpenAPI Spec Parse Error",
            detail=f"Failed to parse OpenAPI yaml specification: {str(exc)}",
        )

    return jsonify(spec_data)


@docs_bp.route("/docs", methods=["GET"])
def get_swagger_ui():
    """Serve Swagger UI interface connected to /openapi.json."""
    return render_template_string(SWAGGER_UI_TEMPLATE, spec_url="/openapi.json")
