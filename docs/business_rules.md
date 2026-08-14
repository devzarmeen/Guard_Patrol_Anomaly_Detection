# Business Rules

## Check-in Rules

### BR-001 — Normal Check-in

A check-in is normal when:

- Correct guard
- Correct site
- Correct shift
- Correct checkpoint
- Within allowed time window
- Valid GPS
- Acceptable GPS accuracy
- Within checkpoint radius

### BR-002 — Late Check-in

If:

actual_time - expected_time > allowed_window

then:

CHECKIN_LATE

### BR-003 — Missed Check-in

If no check-in is received within the configured
waiting period:

CHECKIN_MISSED

---

## Patrol Rules

### BR-004 — Missed Checkpoint

If an expected checkpoint is not completed:

CHECKPOINT_MISSED

### BR-005 — Wrong Checkpoint Sequence

If checkpoints are completed in an unexpected order:

CHECKPOINT_OUT_OF_ORDER

### BR-006 — Route Deviation

If distance between actual movement and expected route
exceeds the configured threshold:

ROUTE_DEVIATION

### BR-007 — Geofence Violation

If guard leaves the permitted geographic area:

GEOFENCE_VIOLATION

---

## GPS Rules

### BR-008 — GPS Accuracy

GPS readings with unacceptable accuracy should not
directly trigger route-deviation alerts.

They should first be classified as:

GPS_DATA_ERROR

### BR-009 — Abnormal Speed

If calculated movement speed exceeds the configured
operational limit:

ABNORMAL_SPEED

---

## Timing Rules

### BR-010 — Suspicious Timing

Repeated or statistically unusual timing patterns
should be flagged for further analysis.

---

## Production Principle

Rules must be configurable and must not be hard-coded
inside model or detection logic.

Thresholds should be evaluated and tuned using
historical labeled incident data.