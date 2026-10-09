import pytest
from tasks_api import create_app
from tasks_api.core.auth import generate_token


@pytest.fixture
def app():
    """Create and configure a testing application instance."""
    app_instance = create_app(config_name="testing")
    yield app_instance


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    """Generate authorization headers with valid Bearer JWT."""
    with app.app_context():
        token = generate_token(user_id="test-engineer-n")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
