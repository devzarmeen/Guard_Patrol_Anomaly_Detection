# Anomaly Detection Approach Comparison

## Overview

Three anomaly detection approaches were evaluated for Guard Patrol monitoring:

1. Rule-Based Detection
2. Isolation Forest Machine Learning Model
3. Hybrid Detection Approach


# 1. Rule-Based Detection

## Description

Uses predefined business rules to identify suspicious guard activity.

Examples:

- Missed check-ins
- Late arrivals
- Abnormal time gaps
- Route deviations

## Advantages

- Highly explainable
- Easy threshold configuration
- Low false positive rate when rules are tuned

## Limitations

- Depends on manually defined rules
- Cannot detect unknown patterns


# 2. Isolation Forest

## Description

Unsupervised machine learning algorithm that detects unusual behavior based on feature patterns.

Features:

- Speed
- Distance changes
- Time gaps
- GPS movement patterns

## Advantages

- Detects unknown anomalies
- No labeled data required

## Limitations

- Less explainable
- Sensitive to threshold selection
- Can generate false positives


# 3. Hybrid Detection

## Description

Combines rule-based detection with ML anomaly scoring.

Architecture:

Rules + Isolation Forest + Risk Scoring


## Advantages

- Better anomaly coverage
- Maintains explainability
- Supports configurable risk thresholds
- Suitable for production monitoring


## Evaluation Results

| Method | Precision | Recall | F1 Score |
|---|---:|---:|---:|
| Rule Based | 1.0 | 1.0 | 1.0 |
| Isolation Forest | 0.0 | 0.0 | 0.0 |
| Hybrid | 0.6667 | 1.0 | 0.8 |


## Final Selection

Hybrid detection is selected as the production architecture because:

- Rule layer provides explainability
- ML layer detects unknown patterns
- Risk scoring allows threshold tuning
- Supports future feedback-based improvement


## Future Improvements

- Increase labeled incident dataset
- Tune thresholds using operator feedback
- Add LSTM Autoencoder for sequence-based GPS anomaly detection
- Monitor false positive rate continuously