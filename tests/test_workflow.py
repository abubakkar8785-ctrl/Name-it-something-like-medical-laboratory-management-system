def test_full_lab_workflow(app, logged_in_client):
    """
    Exercises the whole path: register a patient, create a lab order
    against seeded catalog tests, collect + receive the auto-created
    sample, enter + verify results, confirm the order auto-completes,
    generate a PDF report, and take a payment on the auto-created
    invoice.
    """
    client = logged_in_client

    r = client.post(
        "/patients/new",
        data={"first_name": "John", "last_name": "Doe", "gender": "Male", "phone": "12345"},
        follow_redirects=True,
    )
    assert r.status_code == 200

    with app.app_context():
        from app.models import Patient, TestCatalog

        patient = Patient.query.first()
        assert patient is not None
        catalog_tests = TestCatalog.query.limit(2).all()
        assert len(catalog_tests) == 2  # seeded catalog should be present
        patient_id = patient.id
        test_ids = [t.id for t in catalog_tests]

    r = client.post(
        "/orders/new",
        data={"patient_id": patient_id, "priority": "Routine", "test_ids": test_ids},
        follow_redirects=True,
    )
    assert r.status_code == 200

    with app.app_context():
        from app.models import LabOrder

        order = LabOrder.query.first()
        assert order is not None
        assert order.status == "Pending"
        order_id = order.id
        sample_ids = [s.id for s in order.samples.all()]
        order_test_ids = [ot.id for ot in order.tests.all()]
        invoice_id = order.invoice.id

    assert len(sample_ids) >= 1
    assert len(order_test_ids) == 2

    for sid in sample_ids:
        assert client.post(f"/samples/{sid}/collect", follow_redirects=True).status_code == 200
        assert client.post(f"/samples/{sid}/receive", follow_redirects=True).status_code == 200

    for otid in order_test_ids:
        r = client.post(
            f"/results/entry/{otid}", data={"value": "5.0", "flag": "Normal"}, follow_redirects=True
        )
        assert r.status_code == 200

    with app.app_context():
        from app.models import LabOrderTest

        result_ids = [
            ot.result.id for ot in LabOrderTest.query.all() if ot.result
        ]
    assert len(result_ids) == 2

    for rid in result_ids:
        assert client.post(f"/results/verify/{rid}", follow_redirects=True).status_code == 200

    with app.app_context():
        from app.models import LabOrder

        order = LabOrder.query.get(order_id)
        assert order.status == "Completed"

    r = client.get(f"/reports/order/{order_id}/pdf")
    assert r.status_code == 200
    assert r.data[:4] == b"%PDF"

    r = client.post(
        f"/billing/{invoice_id}/pay", data={"amount": "5", "method": "Cash"}, follow_redirects=True
    )
    assert r.status_code == 200

    r = client.get(f"/reports/invoice/{invoice_id}/pdf")
    assert r.status_code == 200
    assert r.data[:4] == b"%PDF"
