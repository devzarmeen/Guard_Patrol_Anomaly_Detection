from datetime import datetime


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["database"] == "ok"


def test_anomaly_crud_and_metrics(client):
    payload = {
        "guard_id": "G001",
        "timestamp": datetime(2026, 8, 13, 8, 32).isoformat(),
        "latitude": 51.5074,
        "longitude": -0.1278,
        "speed_kmh": 3.2,
        "time_gap_seconds": 5,
        "distance_from_previous_m": 4.1,
        "distance_to_road_m": 8.0,
        "final_hybrid_score": 0.72,
        "final_risk_level": "Critical",
        "final_anomaly": True,
        "anomaly_reason": "Extreme speed",
    }
    created = client.post("/api/anomalies", json=payload)
    assert created.status_code == 200
    anomaly_id = created.json()["id"]

    listed = client.get("/api/anomalies?page=1&limit=10&risk_level=Critical")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    metrics = client.get("/api/metrics")
    assert metrics.json()["critical_anomalies"] == 1

    updated = client.put(
        f"/api/anomalies/{anomaly_id}",
        json={"anomaly_reason": "Updated reason"},
    )
    assert updated.json()["anomaly_reason"] == "Updated reason"


def test_thresholds_endpoint(client):
    current = client.get("/api/config/thresholds")
    assert current.status_code == 200
    assert "checkin" in current.json()


def test_evaluation_endpoint_after_sample_ingest(client):
    ingest = client.post("/api/ingest/sample")
    assert ingest.status_code == 200
    evaluation = client.get("/api/evaluation")
    assert evaluation.status_code == 200
    body = evaluation.json()
    assert "comparison" in body
    assert "methods" in body["comparison"]
    assert body["labeled_examples"] >= 1
    assert set(body["comparison"]["methods"]) == {
        "rule",
        "isolation_forest",
        "hybrid",
    }


def test_incident_operator_feedback(client):
    created = client.post(
        "/api/incidents",
        json={
            "event_id": "EVT-OP-1",
            "guard_id": "G001",
            "anomaly_type": "CHECKIN_LATE",
            "is_incident": False,
            "severity": "LOW",
            "verified_by": "OP001",
            "operator_decision": "False Positive",
        },
    )
    assert created.status_code == 200
    listed = client.get("/api/incidents")
    assert listed.status_code == 200
    assert listed.json()[0]["operator_decision"] == "False Positive"
