# Data Requirements

## 1. Guard Data

Required:

- guard_id
- site_id
- shift_id
- assigned_route_id

---

## 2. Check-in Data

Required:

- checkin_id
- guard_id
- site_id
- checkpoint_id
- expected_time
- actual_time
- latitude
- longitude
- gps_accuracy

---

## 3. GPS Data

Required:

- guard_id
- timestamp
- latitude
- longitude
- accuracy
- speed
- heading (if available)

---

## 4. Patrol Data

Required:

- patrol_id
- guard_id
- route_id
- checkpoint_id
- sequence
- expected_time
- actual_time

---

## 5. Route Data

Required:

- route_id
- site_id
- route geometry
- checkpoint coordinates
- allowed deviation
- expected duration

---

## 6. Incident Data

Required:

- incident_id
- anomaly_id
- guard_id
- anomaly_type
- severity
- is_true_incident
- operator_decision
- resolution
- timestamp

---

## Importance of Incident Labels

A labeled incident dataset is required to measure:

- Precision
- Recall
- F1-score
- False Positive Rate
- False Negative Rate
- Detection latency

The labeled dataset will also be used for threshold
tuning and model comparison.