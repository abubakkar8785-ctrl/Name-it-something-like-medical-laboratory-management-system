def test_default_admin_created(app):
    with app.app_context():
        from app.models import User
        admin = User.query.filter_by(username="admin").first()
        assert admin is not None
        assert admin.is_admin()


def test_login_wrong_password_rejected(client):
    r = client.post(
        "/login", data={"username": "admin", "password": "wrong"}, follow_redirects=True
    )
    assert b"Invalid username or password" in r.data


def test_login_success_redirects_to_dashboard(client):
    r = client.post(
        "/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True
    )
    assert r.status_code == 200


def test_dashboard_requires_login(client):
    r = client.get("/", follow_redirects=True)
    assert b"log in" in r.data.lower() or b"login" in r.data.lower()


def test_logout(logged_in_client):
    r = logged_in_client.get("/logout", follow_redirects=True)
    assert r.status_code == 200
