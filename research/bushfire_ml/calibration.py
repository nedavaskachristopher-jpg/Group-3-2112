"""Small monotone sigmoid and calibration-only threshold selection helpers."""

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logit


def checked_scores(scores, labels=None):
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 1 or not scores.size or not np.isfinite(scores).all() or not ((scores >= 0) & (scores <= 1)).all():
        raise ValueError("A nonempty vector of finite scores in [0, 1] is required")
    if labels is not None:
        labels = np.asarray(labels)
        if labels.shape != scores.shape or not set(np.unique(labels)).issubset({0, 1}):
            raise ValueError("Equally sized binary labels are required")
    return scores


def fit_sigmoid(scores, labels, config):
    """Fit expit(a * logit(score) + b), with a >= 0 and no class reweighting."""
    scores = checked_scores(scores, labels)
    labels = np.asarray(labels, dtype=float)
    if set(np.unique(labels)) != {0, 1}:
        raise ValueError("Sigmoid calibration requires both classes")
    if config["C"] <= 0 or not 0 < config["clip"] < 0.5:
        raise ValueError("Positive regularisation C and a valid clipping epsilon are required")
    logits = logit(np.clip(scores, config["clip"], 1-config["clip"]))

    def objective(parameters):
        slope, intercept = parameters
        linear = slope*logits+intercept
        residual = expit(linear)-labels
        loss = np.logaddexp(0, linear).sum()-np.dot(labels, linear)+slope*slope/(2*config["C"])
        gradient = np.array([np.dot(residual, logits)+slope/config["C"], residual.sum()])
        return loss, gradient

    fitted = minimize(objective, [0.0, float(logit(labels.mean()))], jac=True, method="L-BFGS-B",
                      bounds=[(0, None), (None, None)],
                      options={"maxiter": config["max_iterations"], "ftol": 1e-12, "gtol": 1e-8})
    if not fitted.success or not np.isfinite(fitted.x).all():
        raise RuntimeError(f"Sigmoid optimisation failed: {fitted.message}")
    return {"method": "nondecreasing_regularized_logit_sigmoid", "slope": float(fitted.x[0]),
            "intercept": float(fitted.x[1]), "clip": config["clip"], "C": config["C"],
            "fitting_rows": len(labels), "positive_rows": int(labels.sum()),
            "class_weight": None, "objective": "sum binary log loss + slope^2 / (2*C)"}


def apply_sigmoid(scores, fitted):
    scores = checked_scores(scores)
    if fitted["slope"] < 0:
        raise ValueError("Calibration must not reverse the raw risk ordering")
    logits = logit(np.clip(scores, fitted["clip"], 1-fitted["clip"]))
    return expit(fitted["slope"]*logits+fitted["intercept"])


def select_recall_threshold(scores, labels, target):
    """Select on calibration outcomes only; never split a tied score group."""
    scores = checked_scores(scores, labels)
    labels = np.asarray(labels, dtype=int)
    if not 0 < target <= 1 or not labels.sum():
        raise ValueError("A recall target in (0, 1] and positive selection labels are required")
    # The largest feasible cutoff is an observed positive score. Ties stay together.
    positive_scores = np.sort(scores[labels == 1])[::-1]
    required = int(np.ceil(target*len(positive_scores)))
    threshold = float(positive_scores[required-1])
    decisions = scores >= threshold
    return {"recall_target": target, "threshold": threshold, "comparison": ">=",
            "selection_rows": len(labels), "selection_positives": int(labels.sum()),
            "selection_recall": float(labels[decisions].sum()/labels.sum()),
            "selection_alerts": int(decisions.sum()), "selection_scope": "calibration rows only"}
