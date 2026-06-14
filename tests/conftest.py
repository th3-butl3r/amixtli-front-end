import pytest


@pytest.fixture(scope="session")
def flask_app():
    from app import app as flask_application

    flask_application.config["TESTING"] = True
    flask_application.config["WTF_CSRF_ENABLED"] = False
    return flask_application


@pytest.fixture()
def client(flask_app):
    with flask_app.test_client() as c:
        yield c
