def test_admin_redirected_to_license_page_when_unlicensed(unlicensed_app):
    client = unlicensed_app.test_client()
    client.post(
        "/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True
    )

    r = client.get("/patients/", follow_redirects=True)
    assert r.status_code == 200
    assert b"license" in r.data.lower()


def test_admin_can_still_reach_login_and_logout_when_unlicensed(unlicensed_app):
    client = unlicensed_app.test_client()
    r = client.post(
        "/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True
    )
    assert r.status_code == 200

    r = client.get("/logout", follow_redirects=True)
    assert r.status_code == 200


def test_non_admin_sees_blocked_page_when_unlicensed(unlicensed_app):
    with unlicensed_app.app_context():
        from app.models import db, User

        tech = User(username="tech1", full_name="Lab Tech", role="lab_technician")
        tech.set_password("pass1234")
        db.session.add(tech)
        db.session.commit()

    client = unlicensed_app.test_client()
    client.post(
        "/login", data={"username": "tech1", "password": "pass1234"}, follow_redirects=True
    )

    r = client.get("/patients/", follow_redirects=True)
    assert r.status_code == 403
    assert b"administrator" in r.data.lower()


def test_activating_license_lifts_the_gate(unlicensed_app):
    client = unlicensed_app.test_client()
    client.post(
        "/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True
    )

    # Blocked before activation
    r = client.get("/patients/", follow_redirects=True)
    assert b"license" in r.data.lower()

    from app.license_check import generate_license_key

    key = generate_license_key("Acme Labs", days_valid=365)
    r = client.post("/settings/license", data={"license_key": key}, follow_redirects=True)
    assert r.status_code == 200

    # No longer blocked after activation
    r = client.get("/patients/")
    assert r.status_code == 200
