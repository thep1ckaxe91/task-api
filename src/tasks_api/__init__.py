import logging
import os
from typing import Optional
from flask import Flask

from tasks_api.config import config_by_name, Config
from tasks_api.core.errors import register_error_handlers
from tasks_api.core.docs import docs_bp
from tasks_api.routes.health import health_bp
from tasks_api.routes.tasks import tasks_bp


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Application Factory for tasks-api.
    Initializes Flask application, configuration, error handlers, and blueprints.
    """
    app = Flask(__name__)

    # Determine configuration
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    config_class = config_by_name.get(config_name, Config)
    app.config.from_object(config_class)

    # Configure logging
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    )

    # Register RFC 7807 global error handlers
    register_error_handlers(app)

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(docs_bp)
    app.register_blueprint(tasks_bp)

    return app
