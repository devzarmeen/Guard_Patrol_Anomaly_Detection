# Data Quality Rules

## Check-in Data

- guard_id must not be null.
- site_id must not be null.
- shift_id must not be null.
- checkpoint_id must not be null.
- expected_time must be a valid timestamp.
- actual_time may be null for missed check-ins.
- status must be a valid status.

## GPS Data

- latitude must be between -90 and 90.
- longitude must be between -180 and 180.
- timestamp must be valid.
- accuracy must be greater than or equal to zero.
- duplicate GPS events should be detected.
- impossible GPS jumps should be flagged.

## Patrol Data

- guard_id must not be null.
- patrol_id must not be null.
- checkpoint_id must not be null.
- sequence must be positive.
- expected_time must be valid.
- actual_time may be null if checkpoint was missed.

## Incident Labels

- event_id must identify the related event.
- anomaly_type must be recognized.
- is_incident must be boolean.
- severity must be valid.
- verified_by must identify the reviewer.

## Production Data Quality

The pipeline must track:

- Missing values
- Duplicate events
- Invalid timestamps
- Invalid GPS coordinates
- GPS accuracy problems
- Schema violations
- Out-of-order events
- Impossible movement