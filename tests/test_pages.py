import pytest

PAGES = [
    "/patients/", "/doctors/", "/orders/", "/samples/", "/results/", "/reports/",
    "/billing/", "/inventory/", "/settings/", "/settings/tests", "/settings/users",
    "/settings/backups", "/settings/license",
    "/patients/new", "/doctors/new", "/orders/new", "/inventory/new",
    "/settings/tests/new", "/settings/users/new",
]


@pytest.mark.parametrize("path", PAGES)
def test_page_renders(logged_in_client, path):
    r = logged_in_client.get(path)
    assert r.status_code == 200


def test_inventory_adjustment(logged_in_client, app):
    r = logged_in_client.post(
        "/inventory/new",
        data={"name": "Reagent X", "category": "Reagent", "unit": "ml",
              "quantity_on_hand": "10", "reorder_level": "5"},
        follow_redirects=True,
    )
    assert r.status_code == 200

    with app.app_context():
        from app.models import InventoryItem
        item = InventoryItem.query.first()
        item_id = item.id

    r = logged_in_client.post(
        f"/inventory/{item_id}/adjust",
        data={"transaction_type": "OUT", "quantity": "3", "reason": "used in test"},
        follow_redirects=True,
    )
    assert r.status_code == 200

    with app.app_context():
        from app.models import InventoryItem
        item = InventoryItem.query.get(item_id)
        assert item.quantity_on_hand == 7.0


def test_license_activation(logged_in_client):
    from app.license_check import generate_license_key

    key = generate_license_key("Test Lab Inc", days_valid=365)
    r = logged_in_client.post(
        "/settings/license", data={"license_key": key}, follow_redirects=True
    )
    assert r.status_code == 200
    assert b"activated" in r.data.lower()


def test_backup_download(logged_in_client):
    r = logged_in_client.get("/settings/backup")
    assert r.status_code == 200
    assert len(r.data) > 0
