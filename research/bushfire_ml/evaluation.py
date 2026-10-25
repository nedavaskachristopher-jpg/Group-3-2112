"""Shared score, decision and reliability diagnostics for binary detections."""

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, log_loss


def evaluate(labels, scores, threshold: float, days: int, hard_rule: bool = False) -> dict:
    labels = np.asarray(labels)
    scores = np.asarray(scores, dtype=float)
    if labels.size == 0 or labels.shape != scores.shape or not np.isfinite(scores).all():
        raise ValueError("Nonempty labels and finite, equally sized scores are required")
    if not set(np.unique(labels)).issubset({0, 1}) or not ((0 <= scores) & (scores <= 1)).all():
        raise ValueError("Invalid binary labels or probabilities")
    labels = labels.astype(int)
    if days <= 0:
        raise ValueError("The number of represented days must be positive")
    predictions = (scores >= threshold).astype(int)
    tn, fp, fn, tp = (int(value) for value in confusion_matrix(labels, predictions, labels=[0, 1]).ravel())
    precision = tp/(tp+fp) if tp+fp else 0.0
    recall = tp/(tp+fn) if tp+fn else None
    return {
        "rows": len(labels), "positive_cell_days": int(labels.sum()),
        "average_precision": float(average_precision_score(labels, scores)) if labels.sum() else None,
        "precision": precision, "recall": recall,
        "f1": 2*precision*recall/(precision+recall) if recall is not None and precision+recall else 0.0,
        "accuracy": (tp+tn)/len(labels), "false_positive_rate": fp/(fp+tn) if fp+tn else None,
        "true_positives": tp, "false_positives": fp, "false_negatives": fn, "true_negatives": tn,
        "alert_cell_days": tp+fp, "alerts_per_day": (tp+fp)/days,
        "false_alerts_per_day": fp/days,
        "brier_score": float(brier_score_loss(labels, scores)),
        "log_loss": None if hard_rule else float(log_loss(labels, scores, labels=[0, 1])),
        "score_mean": float(scores.mean()), "threshold": threshold,
        "interpretation": "Hard binary rule; Brier is a 0/1 squared-error reference, not a calibrated probability" if hard_rule
                          else "Uncalibrated probability estimate",
        "zero_alert_precision_convention": "Precision is reported as zero when there are no alerts",
    }


def reliability_bins(labels, probabilities, bins: int) -> list[dict]:
    labels, probabilities = np.asarray(labels), np.asarray(probabilities)
    assignments = np.minimum((probabilities*bins).astype(int), bins-1)
    results = []
    for index in range(bins):
        mask = assignments == index
        if mask.any():
            results.append({"lower": index/bins, "upper": (index+1)/bins,
                            "rows": int(mask.sum()), "mean_probability": float(probabilities[mask].mean()),
                            "observed_rate": float(labels[mask].mean())})
    return results
