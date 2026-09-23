def test_same_origin_post_allowed(logged_in_client):
    """No Origin/Referer header at all — this is what the desktop
    window's own same-origin requests look like, and must keep working."""
    r = logged_in_client.post(
        "/doctors/new", data={"full_name": "Dr. No Header"}, follow_redirects=True
    )
    assert r.status_code == 200


def test_matching_origin_header_allowed(logged_in_client):
    r = logged_in_client.post(
        "/doctors/new",
        data={"full_name": "Dr. Matching Origin"},
        headers={"Origin": "http://localhost"},
        base_url="http://localhost",
        follow_redirects=True,
    )
    assert r.status_code == 200


def test_cross_origin_post_blocked(logged_in_client):
    r = logged_in_client.post(
        "/doctors/new",
        data={"full_name": "Dr. Evil Origin"},
        headers={"Origin": "http://attacker.example"},
    )
    assert r.status_code == 403


def test_cross_origin_referer_blocked(logged_in_client):
    r = logged_in_client.post(
        "/doctors/new",
        data={"full_name": "Dr. Evil Referer"},
        headers={"Referer": "http://attacker.example/evil-page"},
    )
    assert r.status_code == 403


def test_get_requests_not_affected_by_origin_guard(logged_in_client):
    r = logged_in_client.get("/doctors/", headers={"Origin": "http://attacker.example"})
    assert r.status_code == 200
