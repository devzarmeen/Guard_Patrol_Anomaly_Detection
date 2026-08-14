# Phase 2 — Data Architecture

## Purpose

The data architecture defines the structure, relationships,
validation requirements, and storage organization for guard
check-in, GPS, patrol, and incident data.

The architecture must support:

- Historical batch processing
- Incremental data processing
- Future streaming ingestion
- Anomaly detection
- Incident labeling
- False-positive tracking
- Model evaluation

---

# 1. Core Data Domains

The system uses four primary data domains:

1. Check-in Data
2. GPS Data
3. Patrol Data
4. Incident Label Data

---

# 2. Check-in Data

Check-in data represents a guard's check-in activity
at an assigned checkpoint.

## Required Fields

| Field | Description |
|---|---|
| guard_id | Unique guard identifier |
| site_id | Security site identifier |
| shift_id | Guard shift identifier |
| checkpoint_id | Checkpoint identifier |
| expected_time | Scheduled check-in time |
| actual_time | Actual check-in time |
| status | Check-in status |

## Possible Status Values

- NORMAL
- LATE
- MISSED
- INVALID

---

# 3. GPS Data

GPS data represents the guard's geographic movement
over time.

## Required Fields

| Field | Description |
|---|---|
| guard_id | Unique guard identifier |
| timestamp | GPS event timestamp |
| latitude | GPS latitude |
| longitude | GPS longitude |
| accuracy | GPS accuracy in meters |

Optional fields:

- speed
- heading
- altitude
- device_id

---

# 4. Patrol Data

Patrol data represents the expected and actual
checkpoint sequence of a patrol.

## Required Fields

| Field | Description |
|---|---|
| guard_id | Unique guard identifier |
| patrol_id | Unique patrol identifier |
| checkpoint_id | Checkpoint identifier |
| expected_time | Expected checkpoint time |
| actual_time | Actual checkpoint time |
| sequence | Expected checkpoint sequence |

Optional fields:

- route_id
- site_id
- distance_from_route
- checkpoint_status

---

# 5. Incident Labels

Incident labels represent verified anomaly outcomes.

## Required Fields

| Field | Description |
|---|---|
| event_id | Unique event identifier |
| guard_id | Guard identifier |
| anomaly_type | Detected anomaly type |
| is_incident | Verified incident status |
| severity | Incident severity |
| verified_by | Person/system that verified the event |

Optional fields:

- incident_id
- operator_decision
- resolution
- verification_timestamp
- notes

---

# 6. Data Relationship

Guard
  |
  +---- Check-in Events
  |
  +---- GPS Events
  |
  +---- Patrol Events
  |
  +---- Incident Labels

Site
  |
  +---- Guards
  +---- Checkpoints
  +---- Routes
  +---- Patrols

---

# 7. Data Processing Lifecycle

Raw Data
    ↓
Schema Validation
    ↓
Data Quality Validation
    ↓
Cleaning
    ↓
Standardization
    ↓
Processed Data
    ↓
Feature Engineering
    ↓
Anomaly Detection

---

# 8. Production Requirements

The architecture must support:

- Incremental data ingestion
- Historical data processing
- Configurable schemas
- Data validation
- Missing-value detection
- Duplicate detection
- Timestamp validation
- GPS coordinate validation
- Data quality monitoring
- Incident labeling
- False-positive tracking