import os
import sys
import shutil
import tempfile
import pytest


def _build_isolated_app():
    """
    Creates a Flask app pointed at a fresh temp data directory, fully
    isolated from real user data and from other test runs. Returns
    (flask_app, cleanup_fn).
    """
    temp_dir = tempfile.mkdtemp(prefix="medlab_test_")
    old_data_dir = os.environ.get("MEDLAB_DATA_DIR")
    os.environ["MEDLAB_DATA_DIR"] = temp_dir

    # Config/get_data_dir() are read at import time in some modules,
    # so make sure we import app fresh after setting the env var.
    for mod in list(sys.modules):
        if mod == "app" or mod.startswith("app."):
            del sys.modules[mod]

    from app import create_app
    flask_app = create_app()
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    def cleanup():
        if old_data_dir is not None:
            os.environ["MEDLAB_DATA_DIR"] = old_data_dir
        else:
            os.environ.pop("MEDLAB_DATA_DIR", None)
        shutil.rmtree(temp_dir, ignore_errors=True)

    return flask_app, cleanup


@pytest.fixture
def app():
    """
    Fresh, isolated Flask app with a valid test license already
    activated -- this is what every ordinary test should use, since
    without an active license the license-enforcement gate (see
    app/__init__.py::_register_license_gate) blocks everything except
    login and the license-activation page itself.
    """
    flask_app, cleanup = _build_isolated_app()

    with flask_app.app_context():
        from app.license_check import activate_license, generate_license_key
        activate_license(generate_license_key("Test Suite", days_valid=3650))

    yield flask_app
    cleanup()


@pytest.fixture
def unlicensed_app():
    """
    Same as `app`, but with no license activated -- for testing the
    license-enforcement gate itself (test_license_gating.py). Don't
    use this for anything else; every other test expects normal access.
    """
    flask_app, cleanup = _build_isolated_app()
    yield flask_app
    cleanup()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=True,
    )
    return client
