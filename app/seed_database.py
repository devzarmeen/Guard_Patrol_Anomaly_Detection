import csv
from datetime import datetime

from sqlmodel import Session

from pathlib import Path

from app.database import engine, create_tables
from app.models import AnomalyPoint, ActionableEvent

ROOT = Path(__file__).resolve().parent.parent


ANOMALY_FILE = ROOT / "notebooks" / "final_anomaly_points.csv"
EVENT_FILE = ROOT / "notebooks" / "final_actionable_events.csv"


def import_anomaly_points():
    if not ANOMALY_FILE.exists():
        print(f"Skipping anomaly import; file not found: {ANOMALY_FILE}")
        return

    with open(ANOMALY_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        with Session(engine) as session:
            count = 0

            for row in reader:
                anomaly = AnomalyPoint(
                    guard_id=row["guard_id"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    speed_kmh=float(row["speed_kmh"]),
                    time_gap_seconds=float(row["time_gap_seconds"]),
                    distance_from_previous_m=float(
                        row["distance_from_previous_m"]
                    ),
                    distance_to_road_m=float(row["distance_to_road_m"]),
                    final_hybrid_score=float(row["final_hybrid_score"]),
                    final_risk_level=row["final_risk_level"],
                    final_anomaly=row["final_anomaly"].lower() == "true",
                    anomaly_reason=row["anomaly_reason"],
                )

                session.add(anomaly)
                count += 1

            session.commit()

    print(f"Imported {count} anomaly points")


def import_actionable_events():
    if not EVENT_FILE.exists():
        print(f"Skipping event import; file not found: {EVENT_FILE}")
        return

    with open(EVENT_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        with Session(engine) as session:
            count = 0

            for row in reader:
                event = ActionableEvent(
                    guard_id=row["guard_id"],
                    patrol_id=row["patrol_id"],
                    session_number=int(row["session_number"]) if row["session_number"] else 0,
                    event_id=int(row["event_id"]),
                    start_time=datetime.fromisoformat(row["start_time"]),
                    end_time=datetime.fromisoformat(row["end_time"]),
                    anomaly_points=int(row["anomaly_points"]),
                    event_risk_level=row["event_risk_level"],
                    event_classification=row["event_classification"],
                    max_speed_kmh=float(row["max_speed_kmh"]),
                    max_distance_jump_m=float(row["max_distance_jump_m"]),
                    max_distance_to_road_m=float(
                        row["max_distance_to_road_m"]
                    ),
                    max_hybrid_score=float(row["max_hybrid_score"]),
                    description=row["description"],
                    alert_status=row["alert_status"],
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                )

                session.add(event)
                count += 1

            session.commit()

    print(f"Imported {count} actionable events")


if __name__ == "__main__":
    create_tables()
    import_anomaly_points()
    import_actionable_events()

    print("Database seeding completed successfully!")