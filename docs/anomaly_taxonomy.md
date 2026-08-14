# Anomaly Taxonomy

## 1. Check-in Anomalies

### CHECKIN_LATE

Guard checked in after the configured acceptable
check-in window.

### CHECKIN_MISSED

Expected check-in was not received within the
configured waiting period.

---

## 2. Patrol Anomalies

### CHECKPOINT_MISSED

Guard failed to visit an expected checkpoint.

### CHECKPOINT_OUT_OF_ORDER

Guard visited checkpoints in an unexpected sequence.

### PATROL_DURATION_ANOMALY

Patrol duration is significantly different from the
expected duration.

---

## 3. GPS Anomalies

### GPS_DATA_ERROR

GPS data is invalid, missing, duplicated, corrupted,
or has unacceptable accuracy.

### ABNORMAL_SPEED

Calculated movement speed is outside the expected
operational range.

### ROUTE_DEVIATION

Guard's actual movement significantly deviates from
the expected patrol route.

### GEOFENCE_VIOLATION

Guard moves outside the permitted operational area.

---

## 4. Timing Anomalies

### SUSPICIOUS_TIMING

Guard activity exhibits unusual or suspicious timing
patterns.

---

## 5. Behavioral Anomalies

### BEHAVIORAL_ANOMALY

A sequence or combination of events significantly
differs from the guard's expected behavioral pattern.