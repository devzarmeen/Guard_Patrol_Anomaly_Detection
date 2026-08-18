# Guard Patrol Anomaly Detection
# Detection Approach Comparison

## 1. Overview

The Guard Patrol Anomaly Detection system uses three detection approaches:

1. Rule-Based Detection
2. Isolation Forest
3. Hybrid Detection

The purpose of this comparison is to evaluate these approaches using labeled incident data and select the most suitable approach based on measurable performance.

The system analyzes:

- GPS movement
- Guard speed
- Time gaps
- Distance jumps
- Road deviation
- Check-in behavior
- Patrol checkpoint behavior

---

## 2. Rule-Based Detection

### How it works

The rule-based detector uses configurable business thresholds to identify suspicious behavior.

Examples include:

- High speed
- Very high speed
- Extreme speed
- Large GPS jump
- Long time gap
- Critical time gap
- Large road deviation

Each triggered rule contributes to the anomaly score.

### Advantages

- Easy to understand
- Easy to explain to security operators
- Configurable thresholds
- Fast execution
- Suitable for known business rules
- Good interpretability

### Limitations

- Depends on manually configured thresholds
- May not detect unknown anomaly patterns
- Thresholds require continuous tuning

---

## 3. Isolation Forest

### How it works

Isolation Forest is an unsupervised machine-learning algorithm.

It identifies observations that are different from the normal GPS behavior.

The model can detect unusual combinations of features such as:

- Speed
- Time gap
- Distance from previous point
- Distance from road

### Advantages

- Does not require a large labeled dataset
- Can detect unusual patterns automatically
- Useful for previously unknown anomalies

### Limitations

- Less explainable than rule-based detection
- Can generate false positives
- Performance depends on feature quality and model configuration
- Requires tuning for the specific guard patrol environment

---

## 4. Hybrid Detection

### How it works

The hybrid detector combines rule-based scoring with machine-learning anomaly scoring.

The current system uses configurable weights:

- Rule weight: 0.5
- ML weight: 0.5
- Anomaly score threshold: 0.35

This allows known business rules and unknown ML-detected behavior to contribute to the final anomaly decision.

### Advantages

- Combines explainability with machine learning
- Can detect known and unusual behavior
- Configurable
- More flexible than using only one detector

### Limitations

- More complex than rule-based detection
- Requires tuning of rule and ML weights
- Can increase false positives if the ML component is not calibrated correctly

---

## 5. Evaluation Metrics

The system evaluates the approaches using:

### Precision

Precision measures how many detected anomalies were actually incidents.

Higher precision means fewer false alarms.

### Recall

Recall measures how many actual incidents were detected.

Higher recall means fewer missed incidents.

### F1 Score

F1 combines precision and recall into one metric.

A higher F1 score indicates a better balance between detecting incidents and avoiding false alarms.

### False Positive Rate

False Positive Rate measures the percentage of normal events incorrectly classified as anomalies.

For a guard monitoring system, keeping this value low is important because excessive false alerts can reduce operator trust.

---

## 6. Current Evaluation Results

The current evaluation uses 3 labeled examples.

| Method | Precision | Recall | F1 Score | False Positive Rate |
|---|---:|---:|---:|---:|
| Rule-Based | 1.000 | 1.000 | 1.000 | 0.000 |
| Isolation Forest | 0.000 | 0.000 | 0.000 | 1.000 |
| Hybrid | 0.667 | 1.000 | 0.800 | 1.000 |

### Confusion Matrix Results

#### Rule-Based

- True Positives: 2
- False Positives: 0
- True Negatives: 1
- False Negatives: 0

#### Isolation Forest

- True Positives: 0
- False Positives: 1
- True Negatives: 0
- False Negatives: 2

#### Hybrid

- True Positives: 2
- False Positives: 1
- True Negatives: 0
- False Negatives: 0

---

## 7. Current Best Method

Based on the current labeled dataset, the Rule-Based approach achieved the highest F1 score:

- Precision: 1.000
- Recall: 1.000
- F1: 1.000
- False Positive Rate: 0.000

Therefore, the evaluation system currently selects:

**Best Method: Rule-Based**

However, this result should be considered preliminary because the current evaluation dataset contains only 3 labeled examples.

A larger verified incident dataset is required before making a final production model-selection decision.

---

## 8. Production Recommendation

The system should continue supporting all three approaches.

The recommended production architecture is:

**Rule-Based + Isolation Forest + Hybrid**

Rules provide explainability and business control.

Isolation Forest provides unsupervised detection of unusual behavior.

Hybrid detection provides a flexible combination of both approaches.

The rule and ML weights should be tuned using a larger labeled incident dataset.

The system should continuously monitor:

- Precision
- Recall
- F1 Score
- False Positive Rate
- False Negative Rate

These metrics should be reviewed as verified incidents and operator decisions become available.

---

## 9. Future Evaluation Improvements

The current labeled dataset is small.

For stronger evaluation, the project should collect more verified incidents containing:

- Guard ID
- Event ID
- Anomaly type
- Incident status
- Severity
- Operator decision
- Verification timestamp

The evaluation dataset should contain both:

- Confirmed incidents
- Confirmed normal events

This will allow more reliable measurement of false positives and false negatives.

---

## 10. Conclusion

The project does not depend on a single arbitrarily selected anomaly detection model.

Three approaches are implemented and evaluated:

1. Rule-Based
2. Isolation Forest
3. Hybrid

The evaluation pipeline calculates measurable performance metrics and automatically identifies the best-performing method based on the labeled dataset.

The current evaluation favors the Rule-Based approach because it achieves perfect performance on the small available labeled dataset.

However, the Hybrid approach remains important for production because it combines explainable business rules with machine-learning-based anomaly detection.

Future tuning should be performed using a larger verified incident dataset.