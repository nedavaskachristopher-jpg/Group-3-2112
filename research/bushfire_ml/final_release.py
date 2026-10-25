"""One authorised final release; subsequent commands return cached results only."""

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve

from .data import LOCAL_ROOT, ROOT, sha256
from .final_metrics import KEYS, final_results, predict_frozen, validate_population
from .final_reporting import write_final_report
from .freeze_final import MANIFEST_PATH, git_output, text_sha256, verify_freeze

RELEASE_DIR = LOCAL_ROOT / "final_evaluation_v1"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_receipt(path, receipt):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
    temporary.replace(path)


def finish_reporting(result, receipt, receipt_path):
    write_final_report(result)
    receipt.update(status="completed", completed_at_utc=utc_now())
    receipt.pop("error", None)
    write_receipt(receipt_path, receipt)
    (ROOT / "reports/final_release.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")


def summary(result, cached):
    return {"cached_result_only": cached, "freeze_commit": result["freeze_commit"],
            "population": result["all_rows"]["population"],
            "model_ap": {key: values["average_precision"] for key, values in result["all_rows"]["models"].items()},
            "policies": {key: {metric: row[metric] for metric in ["threshold", "precision", "recall", "true_positives", "false_positives", "false_negatives", "alerts_per_day"]}
                         for key, row in result["all_rows"]["policies"].items()},
            "no_current_detection_policies": None if result["no_current_detection"] is None else {
                key: {metric: row[metric] for metric in ["recall", "true_positives", "false_positives", "false_negatives"]}
                for key, row in result["no_current_detection"]["policies"].items()},
            "fitting_performed": False, "holdout_evaluated": True}


def main():
    receipt_path = RELEASE_DIR / "release_receipt.json"
    aggregate_path = ROOT / "reports/final_holdout.json"
    public_receipt = ROOT / "reports/final_release.json"
    if not receipt_path.exists() and public_receipt.exists():
        # A fresh checkout may contain published results without ignored local state.
        receipt_path = public_receipt
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt["status"] not in {"metrics_cached", "completed"}:
            raise RuntimeError("Final release already started; refuse to reopen the holdout or repeat prediction")
        if sha256(aggregate_path) != receipt["aggregate_sha256"]:
            raise RuntimeError("Cached aggregate changed; do not replace it by rerunning the holdout")
        result = json.loads(aggregate_path.read_text())
        if receipt["status"] == "metrics_cached":
            finish_reporting(result, receipt, receipt_path)
        print(json.dumps(summary(result, cached=True), indent=2))
        return

    if aggregate_path.exists():
        raise RuntimeError("Final aggregates already exist without a receipt; refuse a new holdout release")

    frozen = verify_freeze(require_committed=True)
    RELEASE_DIR.mkdir(exist_ok=True)
    freeze_commit = git_output("log", "-1", "--format=%H", "--", MANIFEST_PATH.relative_to(ROOT).as_posix())
    if not freeze_commit:
        raise RuntimeError("A committed final freeze is required")
    receipt = {"status": "started", "started_at_utc": utc_now(), "freeze_commit": freeze_commit,
               "freeze_manifest_sha256": text_sha256(MANIFEST_PATH),
               "test_file_sha256": frozen["data_hashes"]["holdout/final_test.csv"],
               "evaluation_runs": 1, "test_csv_reads": 1,
               "authorization": "Explicit user request to freeze both research cutoffs and perform one final evaluation"}
    # Claim release before the first parse; a crash cannot silently restore blind status.
    with receipt_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, indent=2)+"\n")
    try:
        columns = sorted(set(KEYS+ ["park_area_fraction"] + [column for spec in frozen["models"].values() for column in spec["columns"]]))
        frame = pd.read_csv(LOCAL_ROOT / "holdout/final_test.csv", usecols=columns)
        validate_population(frame, frozen)
        scores = predict_frozen(frame, frozen)
        prediction = frame[KEYS].copy()
        for key, values in scores.items():
            prediction[key+"_score"] = np.asarray(values, dtype=float)
        prediction_path = RELEASE_DIR / "final_predictions.csv"
        prediction.to_csv(prediction_path, index=False, float_format="%.17g", lineterminator="\n")
        result = {
            "experiment": frozen["configuration"]["experiment"], "freeze_commit": freeze_commit,
            "freeze_manifest_sha256": receipt["freeze_manifest_sha256"], "evaluated_at_utc": utc_now(),
            "configuration": frozen["configuration"], "frozen_policies": frozen["policies"],
            "frozen_model_hashes": {key: spec["sha256"] for key, spec in frozen["models"].items()},
            "test_sha256": receipt["test_file_sha256"], "prediction_sha256": sha256(prediction_path),
            "prior_information": frozen["prior_information"], "availability_assumption": frozen["availability_assumption"],
            **final_results(frame, scores, frozen), "pr_curves": {},
            "fitting_performed": False, "calibration": None, "thresholds_adjusted_after_release": False,
            "holdout_evaluated": True,
        }
        if frame.fire_positive.sum():
            for key, values in scores.items():
                precision, recall, _ = precision_recall_curve(frame.fire_positive, values)
                count = min(frozen["configuration"]["pr_display_max_points"], len(recall))
                indices = np.unique(np.linspace(0, len(recall)-1, count, dtype=int))
                result["pr_curves"][key] = {"precision": precision[indices].tolist(), "recall": recall[indices].tolist()}
        aggregate_path.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
        receipt.update(status="metrics_cached", aggregate_sha256=sha256(aggregate_path),
                       predictions_sha256=sha256(prediction_path), metrics_cached_at_utc=utc_now())
        write_receipt(receipt_path, receipt)
        finish_reporting(result, receipt, receipt_path)
    except Exception as error:
        if receipt["status"] not in {"metrics_cached", "completed"}:
            receipt["status"] = "failed_after_release_started"
        receipt["error"] = f"{type(error).__name__}: {error}"
        write_receipt(receipt_path, receipt)
        raise
    print(json.dumps(summary(result, cached=False), indent=2))


if __name__ == "__main__":
    main()
