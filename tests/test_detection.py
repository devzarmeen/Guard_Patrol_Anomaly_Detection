from datetime import datetime, timedelta

from app.detection.features import build_gps_features
from app.detection.hybrid import detect_hybrid
from app.detection.isolation_forest import detect_isolation_forest
from app.detection.patrols import detect_patrols
from app.detection.rules import detect_rule_based
from app.geo import haversine_meters


def test_haversine_is_not_raw_lat_lon_difference():
    distance = haversine_meters(51.5074, -0.1278, 51.5074, -0.1178)
    assert 600 < distance < 800


def test_rule_if_and_hybrid_run_on_gps_features():
    start = datetime(2026, 8, 13, 8, 30)
    rows = [
        {
            "guard_id": "G001",
            "timestamp": start,
            "latitude": 51.5074,
            "longitude": -0.1278,
            "speed": 3.0,
            "distance_to_road_m": 5,
        },
        {
            "guard_id": "G001",
            "timestamp": start + timedelta(seconds=5),
            "latitude": 51.51,
            "longitude": -0.13,
            "speed": 90.0,
            "distance_to_road_m": 220,
        },
        {
            "guard_id": "G001",
            "timestamp": start + timedelta(minutes=20),
            "latitude": 51.52,
            "longitude": -0.14,
            "speed": 4.0,
            "distance_to_road_m": 8,
        },
    ]
    features = build_gps_features(rows)
    rule_points = detect_rule_based(features)
    if_points = detect_isolation_forest(features)
    hybrid_points = detect_hybrid(features)
    assert any(point.is_anomaly for point in rule_points)
    assert len(if_points) == 3
    assert len(hybrid_points) == 3


def test_out_of_order_checkpoint_detection():
    findings = detect_patrols(
        [
            {
                "patrol_id": "P001",
                "guard_id": "G001",
                "checkpoint_id": "CP001",
                "sequence": 1,
                "expected_time": "2026-08-13T08:30:00",
                "actual_time": "2026-08-13T08:50:00",
            },
            {
                "patrol_id": "P001",
                "guard_id": "G001",
                "checkpoint_id": "CP002",
                "sequence": 2,
                "expected_time": "2026-08-13T08:45:00",
                "actual_time": "2026-08-13T08:40:00",
            },
        ]
    )
    types = {item["anomaly_type"] for item in findings}
    assert "CHECKPOINT_OUT_OF_ORDER" in types


def test_gps_features_use_context_rows_for_incremental_gaps():
    start = datetime(2026, 8, 13, 8, 30)
    context = [
        {
            "guard_id": "G001",
            "timestamp": start,
            "latitude": 51.5074,
            "longitude": -0.1278,
        }
    ]
    rows = [
        {
            "guard_id": "G001",
            "timestamp": start + timedelta(seconds=5),
            "latitude": 51.52,
            "longitude": -0.14,
            "speed": 80.0,
        }
    ]
    without_context = build_gps_features(rows)
    with_context = build_gps_features(rows, context_rows=context)
    assert without_context[0].distance_from_previous_m == 0.0
    assert with_context[0].distance_from_previous_m > 1000
