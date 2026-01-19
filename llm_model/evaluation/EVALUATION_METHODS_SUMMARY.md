# Evaluation Methods Summary for Slides

## Evaluation Framework Overview

| Component | Key Metrics | Evaluation Dimensions | Missing GT Handling |
|-----------|-------------|----------------------|---------------------|
| **Characters** | Precision, Recall, F1<br>Archetype Accuracy | Name matching (exact/fuzzy)<br>Archetype classification<br>Completeness | Extra characters not penalized if GT empty |
| **Relationships** | Precision, Recall, F1<br>Level 1/2 Accuracy<br>Pair Coverage | Relationship classification<br>Agent-target pairs<br>Hierarchical structure | Empty GT relationships → skip evaluation, no penalty |
| **Sentiment** | Precision, Recall, F1<br>Polarity Accuracy | Sentiment labels<br>Polarity consistency<br>Multi-value support | Empty GT sentiment → mark incomplete, exclude from denominator |
| **Action Layer** | Field-wise Accuracy<br>Complete/Partial Match | Category, Type, Context<br>Status, Function<br>Hierarchical taxonomy | Only evaluate fields present in GT; missing fields not penalized |
| **Text Span** | Boundary Score<br>Overlap Ratio<br>Exact/Near Matches | Boundary segmentation<br>Character position → sentence index<br>IoU-like overlap | Null GT spans → exclude from boundary calculation, no insertion penalty |

## Key Features

| Feature | Description |
|---------|-------------|
| **Missing GT Strategy** | Predictions for missing GT fields are not counted as false positives |
| **Partial Evaluation** | Only evaluate fields present in GT; missing fields excluded from denominator |
| **Boundary Metric** | Uses same algorithm as text segmentation module (Boundary Segmentation Metric) |
| **Hierarchical Matching** | Supports multi-level classification (Level 1/2 for relationships, taxonomy for actions) |
| **Composite Scoring** | Aggregates all component scores into overall evaluation report |

## Evaluation Metrics Formula

| Metric | Formula | Notes |
|--------|---------|-------|
| **Precision** | TP / (TP + FP) | FP excludes predictions for missing GT fields |
| **Recall** | TP / (TP + FN) | Denominator excludes missing GT data points |
| **F1 Score** | 2 × (P × R) / (P + R) | Harmonic mean of precision and recall |
| **Boundary Score** | Boundary Segmentation Metric | 0-1 score based on sentence boundary alignment |

## Data Sources

| Standard | File Path | Purpose |
|----------|-----------|---------|
| **Relationship Taxonomy** | `docs/Character_Resources/relationship_en.csv` | Level 1/2 classification standards |
| **Sentiment Labels** | `docs/Character_Resources/sentiment.csv` | Sentiment classification standards |
| **Action Taxonomy** | `docs/Universal Narrative Action Taxonomy/` | Action layer classification standards |
| **Ground Truth** | `datasets/*/json_v3/*.json` | Reference annotations |
