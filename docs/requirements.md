# Guard Patrol Anomaly Detection
# Business & System Requirements

## 1. Guard Check-in Requirements

### 1.1 Normal Check-in

A guard check-in is considered normal when the guard
successfully checks in at the assigned checkpoint within
the allowed time window and the associated GPS location
is valid and sufficiently close to the checkpoint.

### Required Information

Each check-in event should contain:

| Field             | Description |
|---                |---          |
| guard_id          | Unique identifier of the guard |
| site_id           | Identifier of the assigned security site |
| checkpoint_id     | Identifier of the checkpoint |
| shift_id          | Identifier of the guard's shift |
| expected_time     | Scheduled check-in time |
| actual_time       | Time when the guard actually checked in |
| latitude          | GPS latitude at check-in |
| longitude         | GPS longitude at check-in |
| gps_accuracy      | GPS accuracy in meters |

### Normal Check-in Conditions

A check-in is considered normal when all of the
following conditions are satisfied:

1. The guard is assigned to the site.
2. The guard is assigned to the current shift.
3. The checkpoint belongs to the assigned patrol route.
4. The check-in occurs within the allowed time window.
5. GPS coordinates are valid.
6. GPS accuracy is within the acceptable limit.
7. The guard's GPS location is sufficiently close to
   the assigned checkpoint.

### Example

Expected check-in:

- Guard: G001
- Site: SITE_001
- Checkpoint: CP_03
- Expected time: 08:30

Actual check-in:

- Actual time: 08:32
- GPS accuracy: 8 meters
- Location: within the allowed checkpoint radius

# Result:

NORMAL CHECK-IN

### Initial Development Assumptions

The following values are initial development assumptions
and must be configurable:

- Allowed check-in window: ±10 minutes
- Maximum acceptable GPS accuracy: 50 meters
- Checkpoint proximity radius: 100 meters

These values must not be hard-coded in the detection
logic.


---

## 1.2 Late Check-in

A check-in is considered late when the guard checks in
after the configured acceptable check-in window but the
check-in is still received within the operational
monitoring period.

### Calculation

Check-in delay is calculated as:

delay = actual_checkin_time - expected_checkin_time

A positive delay indicates that the guard checked in
after the expected time.

### Initial Development Rule

A check-in is considered late when:

delay > 10 minutes

### Examples

Expected: 08:30
Actual: 08:35

Delay: 5 minutes

Result:
NORMAL

---

Expected: 08:30
Actual: 08:42

Delay: 12 minutes

Result:
LATE CHECK-IN

### Important Boundary

Expected: 08:30
Actual: 08:40

Delay: 10 minutes

# Result:
NORMAL

Expected: 08:30
Actual: 08:41

Delay: 11 minutes

# Result:
LATE CHECK-IN

The 10-minute threshold is configurable.


---

## 1.3 Missed Check-in

A check-in is considered missed when the expected
check-in event is not received within the configured
maximum waiting period.

### Initial Development Rule

A check-in is considered missed when:

- No check-in is received within 30 minutes after the
  expected check-in time.

### Example

Expected:
08:30

No check-in received until:
09:00

Result:
MISSED CHECK-IN

### Difference Between Late and Missed

# Late:

08:30 expected
08:42 actual

# Result:
LATE CHECK-IN

# Missed:

08:30 expected
No event until 09:00

# Result:
MISSED CHECK-IN

The missed-check-in threshold must be configurable.

---

## 2. Patrol Requirements

### 2.1 Expected Patrol

An expected patrol is a predefined sequence of
checkpoints that a guard is required to visit during
an assigned patrol shift.

# An expected patrol contains:

- patrol_id
- guard_id
- site_id
- shift_id
- route_id
- checkpoint sequence
- expected checkpoint times
- allowed checkpoint radius

### Example

# Patrol:

CP01 → CP02 → CP03 → CP04 → CP05

# Expected sequence:

1. CP01
2. CP02
3. CP03
4. CP04
5. CP05

# The system should monitor whether the guard:

1. Visits the required checkpoints.
2. Visits them in the expected order.
3. Completes the patrol within the expected duration.
4. Remains within the permitted route/geofence.

---

## 2.2 Route

A patrol route is the predefined geographic path that
a guard is expected to follow while completing a patrol.

# A route consists of:

- route_id
- site_id
- checkpoints
- checkpoint sequence
- geographic geometry
- allowed deviation
- expected duration

### Example

Route R001:

CP01 → CP02 → CP03 → CP04

The actual GPS trajectory of the guard will later be
compared against the expected route.

### Route Data

The route may be represented using:

- GPS coordinates
- LineString geometry
- OpenStreetMap road network
- Checkpoint coordinates
- Geofence boundaries

---

## 2.3 Acceptable GPS Deviation

GPS deviation represents the distance between the
guard's actual GPS position and the expected patrol
route or checkpoint.

### Initial Development Assumption

Checkpoint proximity:

100 meters

Route deviation:

200 meters

### Interpretation

0–100 meters:
Normal

100–200 meters:
Potential deviation depending on route geometry

Greater than 200 meters:
Potential route deviation anomaly

### Important

GPS deviation must not be determined using a simple
latitude/longitude difference.

The production system should calculate geographic
distance using appropriate geospatial methods and,
where available, OpenStreetMap road-network geometry.

GPS accuracy must also be considered because poor GPS
accuracy can produce false route-deviation alerts.

---

## 2.4 Suspicious Timing

Suspicious timing refers to guard activity that
significantly differs from expected operational timing.

# Examples include:

1. Repeatedly checking in at exactly unusual times.
2. Extremely short patrol duration.
3. Extremely long patrol duration.
4. Multiple checkpoints completed unrealistically quickly.
5. Repeated late check-ins.
6. Activity occurring outside the assigned shift.
7. Unusual gaps between consecutive GPS events.
8. Unexpected changes in normal patrol timing patterns.

### Initial Development Approach

Timing anomalies will initially be detected using
rule-based and statistical methods.

Later, machine-learning models may identify more complex
behavioral patterns.
