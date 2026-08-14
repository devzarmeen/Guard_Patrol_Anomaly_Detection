# Business Response Workflow

## Anomaly Lifecycle

Detection
    ↓
Risk Scoring
    ↓
Alert Generation
    ↓
Operator Review
    ↓
Incident Classification
    ↓
Resolution
    ↓
Feedback

---

## 1. Detection

The anomaly detection system identifies a potentially
abnormal event.

Example:

ROUTE_DEVIATION

---

## 2. Risk Scoring

The system assigns:

- anomaly score
- severity
- confidence
- anomaly type

---

## 3. Alert

If the anomaly crosses the configured alert threshold,
the system generates an alert.

Possible channels:

- Webhook
- Email
- Dashboard

---

## 4. Operator Review

An operator reviews:

- Guard
- Location
- Time
- Route
- Check-in history
- GPS history
- Anomaly reason
- Anomaly score

---

## 5. Incident Classification

The operator classifies the event as:

- True Incident
- False Positive
- Needs Investigation

---

## 6. Resolution

The incident is resolved and the resolution is recorded.

---

## 7. Feedback

Verified incident labels are stored for future:

- Threshold tuning
- Model evaluation
- False-positive analysis
- Model improvement