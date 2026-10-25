"""Compare shallow XGBoost with preserved, feature-matched logistic baselines."""

import json

import numpy as np
import pandas as pd
import xgboost
from sklearn.metrics import average_precision_score

from .data import LOCAL_ROOT, ROOT, load_development, model_matrix, sha256, verify_seal
from .evaluation import evaluate, reliability_bins
from .models import fit_xgboost
from .reporting import write_xgboost_report

CONFIG_PATH = ROOT / "config" / "xgboost_v1.json"
NAMES = {"logistic_16": "Logistic 16", "logistic_17": "Logistic 17",
         "xgboost_16": "XGBoost 16", "xgboost_17": "XGBoost 17", "persistence": "Persistence"}


def load_reference_scores(validation, seal):
    """Align preserved predictions without fitting or changing the references."""
    paths = [ROOT / "reports" / "baseline_validation.json", ROOT / "reports" / "current_fire_comparison.json"]
    reports = [json.loads(path.read_text()) for path in paths]
    if any(report["data_hashes"] != seal["file_sha256"] for report in reports):
        raise RuntimeError("Reference reports do not match the frozen data")
    prediction_paths = [LOCAL_ROOT / report["experiment"] / "validation_predictions.csv" for report in reports]
    reference_hashes = {str(path.relative_to(ROOT)): sha256(path) for path in [*paths, *prediction_paths]}
    keys = ["grid_id", "feature_date", "target_date", "fire_positive", "fire_today"]
    aligned = validation[keys]
    for path in prediction_paths:
        prediction = pd.read_csv(path)
        aligned = aligned.merge(prediction, on=keys, validate="one_to_one")
        if len(aligned) != len(validation) or len(prediction) != len(validation):
            raise ValueError("Reference predictions have different validation rows")
    return {
        "logistic_16": aligned.logistic_core_score.to_numpy(),
        "logistic_17": aligned.uncalibrated_score.to_numpy(),
        "persistence": aligned.persistence_score.to_numpy(),
    }, reference_hashes


def main() -> None:
    seal = verify_seal()
    config = json.loads(CONFIG_PATH.read_text())
    training = load_development("train")
    training = training.loc[training.feature_date.gt(config["training_warmup_end_inclusive"])].copy()
    validation = load_development("validation")
    reference_scores, reference_hashes = load_reference_scores(validation, seal)
    local_output = LOCAL_ROOT / config["experiment"]
    local_output.mkdir(exist_ok=True)
    scores, fits = {}, {}
    for feature_set in config["feature_sets"]:
        key = "xgboost_16" if feature_set == "conditions_core" else "xgboost_17"
        model = fit_xgboost(training, validation, config, feature_set)
        prediction = model.predict_proba(model_matrix(validation, feature_set))[:, 1]
        history = model.evals_result()["validation_1"]["average_precision_score"]
        best_ap = float(average_precision_score(validation.fire_positive, prediction))
        if not np.isclose(best_ap, max(history), atol=1e-6):
            raise RuntimeError("Retained model does not maximise validation AP")
        scores[key] = prediction
        fits[key] = {
            "feature_set": feature_set, "feature_count": model.n_features_in_,
            "trees_retained": model.get_booster().num_boosted_rounds(), "rounds_evaluated": len(history),
            "best_validation_ap": best_ap,
            "training_ap": float(average_precision_score(training.fire_positive, model.predict_proba(model_matrix(training, feature_set))[:, 1])),
            "scale_pos_weight": float(model.get_params()["scale_pos_weight"]),
            "learning_history": model.evals_result(),
        }
        model.save_model(local_output / f"{key}.ubj")
    scores = {"logistic_16": reference_scores["logistic_16"], "logistic_17": reference_scores["logistic_17"],
              **scores, "persistence": reference_scores["persistence"]}
    days = int(validation.feature_date.nunique())
    subset = validation.fire_today.eq(0).to_numpy()
    metrics = {key: evaluate(validation.fire_positive, prediction, config["diagnostic_threshold"], days, key == "persistence")
               for key, prediction in scores.items()}
    subsets = {key: evaluate(validation.fire_positive.to_numpy()[subset], prediction[subset], config["diagnostic_threshold"], days, key == "persistence")
               for key, prediction in scores.items()}
    predictions = validation[["grid_id", "feature_date", "target_date", "fire_positive", "fire_today"]].copy()
    for key, prediction in scores.items():
        predictions[key+"_uncalibrated_score"] = prediction
    predictions.to_csv(local_output / "validation_predictions.csv", index=False, lineterminator="\n")
    report = {
        "experiment": config["experiment"], "configuration_sha256": sha256(CONFIG_PATH),
        "xgboost_version": xgboost.__version__, "data_hashes": seal["file_sha256"],
        "reference_file_hashes": reference_hashes, "training_rows": len(training),
        "validation_rows": len(validation), "validation_days": days,
        "diagnostic_threshold": config["diagnostic_threshold"], "fits": fits,
        "validation_metrics": metrics, "fire_today_zero_subset_metrics": subsets,
        "reliability_bins": {key: reliability_bins(validation.fire_positive, prediction, config["calibration_bins"])
                             for key, prediction in scores.items() if key.startswith("xgboost")},
        "notes": [
            "Each algorithm uses the same reviewed input set and observations in its matched comparison. Logistic inputs are scaled; tree inputs are not.",
            "XGBoost uses the training negative/positive ratio for class emphasis, matching the relative class-weight ratio of balanced logistic regression. The objectives and regularisation are not identical.",
            "One prespecified shallow-tree configuration was used. Validation AP selected boosting length through early stopping, so these results are development evidence and can be optimistic.",
            "The stopping metric is sklearn average_precision_score, explicitly maximised. XGBoost's built-in interpolated aucpr is not silently substituted.",
            "Compare persistence and the no-current-detection subset, not just overall ranking or the largest score.",
            "The 0.5 threshold is diagnostic. No probability calibrator or operational alert threshold has been selected.",
            "All labels and validation dates, including the 22 December zero-detection concern, are unchanged.",
            "The nine validation days contain dependent observations. No independent-season or operational performance is established.",
            "AP depends on event prevalence. Compare algorithms on the same evaluation population; the training/validation AP difference alone is not an overfitting diagnosis.",
            "Additional time-aware development checks, calibration design and final pipeline freeze are still required before final-test evaluation."
        ], "holdout_evaluated": False,
    }
    if verify_seal() != seal or any(sha256(ROOT / path) != digest for path, digest in reference_hashes.items()):
        raise RuntimeError("Sealed data or a baseline reference changed during comparison")
    (ROOT / "reports" / "xgboost_comparison.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    write_xgboost_report(report, validation, scores, NAMES)
    print(json.dumps({"validation_metrics": metrics, "fire_today_zero_subset_metrics": subsets,
                      "trees_retained": {key: fit["trees_retained"] for key, fit in fits.items()},
                      "holdout_evaluated": False}, indent=2))


if __name__ == "__main__":
    main()
