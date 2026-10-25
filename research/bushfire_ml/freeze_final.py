"""Freeze existing development artifacts before any final-outcome parsing."""

import hashlib
import importlib.metadata
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import joblib
from xgboost import XGBClassifier

from .data import LOCAL_ROOT, ROOT, load_development, model_matrix, read_protocol, sha256, verify_seal

CONFIG_PATH = ROOT / "config/final_evaluation_v1.json"
MANIFEST_PATH = ROOT / "reports/final_freeze.json"
SNAPSHOT_DIR = LOCAL_ROOT / "frozen_final_v1"


def text_sha256(path):
    """Normalise source newlines so Git CRLF conversion does not change meaning."""
    return hashlib.sha256(Path(path).read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def git_output(*arguments):
    return subprocess.run(["git", *arguments], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def software_versions():
    return {"python": platform.python_version(), **{name: importlib.metadata.version(name) for name in
            ["numpy", "pandas", "scikit-learn", "xgboost", "joblib", "matplotlib", "scipy"]}}


def verify_freeze(require_committed=False):
    frozen = json.loads(MANIFEST_PATH.read_text())
    seal = verify_seal()
    if frozen["data_hashes"] != seal["file_sha256"] or frozen["original_protocol_sha256"] != seal["protocol_sha256"]:
        raise RuntimeError("Data seal differs from the frozen final protocol")
    for name, expected in frozen["source_hashes"].items():
        if text_sha256(ROOT / name) != expected:
            raise RuntimeError(f"Frozen source changed: {name}")
    for name, expected in frozen["development_reference_hashes"].items():
        if text_sha256(ROOT / name) != expected:
            raise RuntimeError(f"Development reference changed: {name}")
    for spec in frozen["models"].values():
        if sha256(ROOT / spec["artifact"]) != spec["sha256"]:
            raise RuntimeError("A frozen model artifact changed")
    if software_versions() != frozen["software_versions"]:
        raise RuntimeError("The runtime differs from the frozen environment")
    if require_committed:
        if git_output("status", "--porcelain"):
            raise RuntimeError("Commit the complete freeze before final release")
        relative = MANIFEST_PATH.relative_to(ROOT).as_posix()
        committed = subprocess.run(["git", "show", f"HEAD:{relative}"], cwd=ROOT, check=True, capture_output=True).stdout
        committed_text = committed.decode("utf-8").replace("\r\n", "\n")
        if hashlib.sha256(committed_text.encode()).hexdigest() != text_sha256(MANIFEST_PATH):
            raise RuntimeError("The current commit does not contain this freeze manifest")
    return frozen


def main():
    if MANIFEST_PATH.exists():
        verify_freeze()
        print("Existing final freeze verified; nothing overwritten and no final outcomes read.")
        return
    if any(path.exists() for path in [LOCAL_ROOT / "final_evaluation_v1/release_receipt.json",
                                     ROOT / "reports/final_release.json", ROOT / "reports/final_holdout.json"]):
        raise RuntimeError("Cannot create a new freeze after final release has started")
    seal = verify_seal()
    config = json.loads(CONFIG_PATH.read_text())
    draft_path = ROOT / "reports/draft_probability_policy.json"
    draft = json.loads(draft_path.read_text())
    probability = json.loads((ROOT / "reports/probability_reliability.json").read_text())
    if draft["calibration"] is not None or draft["model"] != config["primary_model"]:
        raise ValueError("The final plan must preserve the reviewed raw-score decision")
    if [p["recall_target"] for p in draft["cutoffs"]] != [0.8, 0.9] or any(p["comparison"] != ">=" for p in draft["cutoffs"]):
        raise ValueError("Preserve both reviewed recall-target policies and their comparison")
    for name, digest in draft["artifact_hashes"].items():
        if sha256(ROOT / name) != digest:
            raise RuntimeError("A development artifact changed before freezing")
    for name, digest in probability["reference_hashes"].items():
        if sha256(ROOT / name) != digest:
            raise RuntimeError("A model-development reference changed before freezing")
    training = load_development("train")
    warmup = probability["configuration"]["warmup_end_inclusive"]
    training = training.loc[training.feature_date.gt(warmup)]
    scenario = next(r for r in probability["scenarios"] if r["name"] == draft["scenario"])
    if len(training) != scenario["base_refitting"]["rows"] or int(training.fire_positive.sum()) != scenario["base_refitting"]["positives"]:
        raise RuntimeError("The reviewed artifacts and training population differ")
    SNAPSHOT_DIR.mkdir(exist_ok=False)
    source_folder = (ROOT / draft["base_artifact"]).parent
    models = {}
    for key in ["logistic_16", "logistic_17", "xgboost_16", "xgboost_17"]:
        suffix = ".ubj" if key.startswith("xgboost") else ".joblib"
        source = source_folder / (key+suffix)
        destination = SNAPSHOT_DIR / source.name
        with destination.open("xb") as stream:
            stream.write(source.read_bytes())
        if sha256(source) != sha256(destination):
            raise RuntimeError("Artifact copy changed bytes")
        if key.startswith("xgboost"):
            model = XGBClassifier()
            model.load_model(destination)
        else:
            model = joblib.load(destination)
        feature_set = "conditions_core" if key.endswith("16") else "core_plus_fire_today"
        columns = list(model_matrix(training, feature_set).columns)
        if list(model.feature_names_in_) != columns:
            raise RuntimeError("Saved model feature order differs from the approved whitelist")
        spec = {"artifact": destination.relative_to(ROOT).as_posix(), "sha256": sha256(destination),
                "feature_set": feature_set, "columns": columns,
                "preprocessing": "Saved training-fitted StandardScaler pipeline" if key.startswith("logistic") else "No scaling",
                "trained_through_feature_date": draft["base_fit_feature_end"], "refitting_rows": len(training)}
        if key.startswith("xgboost"):
            spec["trees"] = model.get_booster().num_boosted_rounds()
            if spec["trees"] != scenario["base_fits"][key]["trees"]:
                raise RuntimeError("Tree count differs from the reviewed artifact")
        models[key] = spec
    source_paths = sorted([* (ROOT / "bushfire_ml").glob("*.py"), * (ROOT / "tests").glob("*.py"),
                           * (ROOT / "config").glob("*.json"), ROOT / "requirements.txt"])
    reference_paths = sorted(p for p in (ROOT / "reports").glob("*.json") if not p.name.startswith("final_"))
    frozen = {
        "freeze_version": "1.0", "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "development_commit": git_output("rev-parse", "HEAD"), "configuration": config,
        "source_hash_mode": "SHA256 of UTF-8 text with universal LF newlines; model/data hashes use exact bytes",
        "source_hashes": {p.relative_to(ROOT).as_posix(): text_sha256(p) for p in source_paths},
        "development_reference_hashes": {p.relative_to(ROOT).as_posix(): text_sha256(p) for p in reference_paths},
        "original_protocol_sha256": seal["protocol_sha256"], "data_hashes": seal["file_sha256"],
        "test_population": seal["partitions"]["final_test"], "grid_ids": sorted(training.grid_id.unique()),
        "minimum_park_area_fraction": read_protocol()["minimum_park_area_fraction"],
        "target": read_protocol()["target"], "availability_assumption": read_protocol()["availability_assumption"],
        "prior_information": seal["prior_information"], "models": models,
        "training_prevalence": float(training.fire_positive.mean()),
        "policies": [{"name": f"recall_{int(row['recall_target']*100)}_policy", **row} for row in draft["cutoffs"]],
        "policy_selection_dates": draft["selection_dates"], "calibration": None,
        "software_versions": software_versions(), "holdout_evaluated_at_freeze": False,
    }
    with MANIFEST_PATH.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(frozen, indent=2)+"\n")
    verify_freeze()
    print(json.dumps({"freeze_manifest": MANIFEST_PATH.relative_to(ROOT).as_posix(),
                      "model_trees": {k: v.get("trees") for k, v in models.items()},
                      "policies": frozen["policies"], "holdout_evaluated": False}, indent=2))


if __name__ == "__main__":
    main()
