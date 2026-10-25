"""Verify public delivery evidence; optional private checks read bytes, not CSV rows."""

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def sha(path, text=False):
    content = path.read_text(encoding="utf-8").encode("utf-8") if text else path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def contained(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Package path leaves the repository: {relative}")
    return path


def check_hashes(root, hashes, text=True):
    for relative, expected in hashes.items():
        path = contained(root, relative)
        if not path.is_file() or sha(path, text=text) != expected:
            raise ValueError(f"Integrity check failed: {relative}")


def check_links(root, paths):
    count = 0
    for path in paths:
        content = path.read_text(encoding="utf-8")
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", content):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            relative = unquote(target.split("#", 1)[0].strip("<>"))
            resolved = (path.parent / relative).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
                raise ValueError(f"Broken local link in {path.relative_to(root)}: {target}")
            count += 1
    return count


def check_claims(root):
    catalogue = json.loads((root / "docs/evidence/claims.json").read_text())
    sources = {}
    for claim in catalogue["claims"]:
        if claim["source"] not in {"research/reports/final_holdout.json", "research/reports/final_freeze.json"}:
            raise ValueError("A numerical claim must use a declared aggregate source")
        if claim["source"] not in sources:
            sources[claim["source"]] = json.loads((root / claim["source"]).read_text())
        value = sources[claim["source"]]
        for key in claim["path"]:
            value = value[key]
        if claim["transform"] == "length":
            value = len(value)
        elif claim["transform"] is not None:
            raise ValueError("Unknown claim transform")
        if value != claim["value"]:
            raise ValueError(f"Claim mismatch: {claim['source']} {claim['path']}")
    return len(catalogue["claims"])


def check_model_table(root, final):
    with (root / "report/tables/final_models.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if [row["model"] for row in rows] != list(final["all_rows"]["models"]):
        raise ValueError("The exported model table omits or reorders a comparison")
    for row in rows:
        expected = final["all_rows"]["models"][row["model"]]
        for field, value in row.items():
            if field != "model" and value != ("" if expected[field] is None else str(expected[field])):
                raise ValueError(f"Model CSV value differs from its aggregate: {row['model']} {field}")


def check_records(path, expected):
    with path.open(encoding="utf-8", newline="") as stream:
        actual = list(csv.DictReader(stream))
    normalised = [{key: "" if value is None else str(value) for key, value in row.items()} for row in expected]
    if actual != normalised:
        raise ValueError(f"CSV records differ from aggregate evidence: {path.name}")


def check_tables(root, final, frozen):
    folder = root / "report/tables"
    check_model_table(root, final)
    fields = ["average_precision", "precision", "recall", "accuracy", "brier_score", "log_loss",
              "true_positives", "false_positives", "false_negatives", "true_negatives", "alerts_per_day", "false_alerts_per_day"]
    expected = []
    for population in ["all_rows", "no_current_detection"]:
        for key, row in final[population]["policies"].items():
            expected.append({"population": population, "policy": key, "threshold": row["threshold"], **{field: row[field] for field in fields}})
    check_records(folder / "final_policies.csv", expected)
    expected = [{"feature_month": month["month"], "rows": month["all_rows"]["population"]["rows"],
                 "positive_targets": month["all_rows"]["population"]["positives"], "policy": key, **{field: row[field] for field in fields}}
                for month in final["monthly"] for key, row in month["all_rows"]["policies"].items()]
    check_records(folder / "monthly_policies.csv", expected)
    check_records(folder / "reliability_bins.csv", final["all_rows"]["models"]["xgboost_17"]["reliability_bins"])
    history = json.loads((root / "research/reports/xgboost_comparison.json").read_text())
    expected = [{"evidence_scope": "development validation used for original tree selection", "model": key,
                 **{field: row[field] for field in fields}} for key, row in history["validation_metrics"].items()]
    check_records(folder / "development_summary.csv", expected)
    partitions = json.loads((root / "research/reports/partition_manifest.json").read_text())["partitions"]
    protocol = json.loads((root / "research/config/protocol_v1.json").read_text())
    expected = [{"partition": key, **partitions[key]} for key in ["train", "validation", "final_test"]]
    gap_rows = protocol["gap_days"]*len(frozen["grid_ids"])
    expected += [{"partition": "gap_before_validation", "rows": gap_rows, "first_feature_date": "2019-12-09", "last_feature_date": "2019-12-15"},
                 {"partition": "gap_before_final", "rows": gap_rows, "first_feature_date": "2019-12-25", "last_feature_date": "2019-12-31"}]
    check_records(folder / "partitions.csv", sorted(expected, key=lambda row: row["first_feature_date"]))
    return 6


def verify(root=ROOT, local_artifacts=False):
    frozen = json.loads((root / "research/reports/final_freeze.json").read_text())
    receipt = json.loads((root / "research/reports/final_release.json").read_text())
    final = json.loads((root / "research/reports/final_holdout.json").read_text())
    if receipt["status"] != "completed" or receipt["evaluation_runs"] != 1 or receipt["test_csv_reads"] != 1:
        raise ValueError("The release receipt must record exactly one completed evaluation")
    if sha(root / "research/reports/final_holdout.json") != receipt["aggregate_sha256"]:
        raise ValueError("Final aggregate no longer matches its release receipt")
    if sha(root / "research/reports/final_freeze.json", text=True) != receipt["freeze_manifest_sha256"]:
        raise ValueError("The committed freeze manifest changed")
    if final["frozen_policies"] != frozen["policies"] or final["fitting_performed"] or final["thresholds_adjusted_after_release"]:
        raise ValueError("Final model-selection integrity failed")
    check_hashes(root / "research", frozen["source_hashes"])
    check_hashes(root / "research", frozen["development_reference_hashes"])
    manifest = json.loads((root / "docs/evidence/delivery_manifest.json").read_text())
    check_hashes(root, manifest["sources"])
    for relative, spec in manifest["files"].items():
        check_hashes(root, {relative: spec["sha256"]}, text=spec["mode"] == "text_lf")
    claims = check_claims(root)
    tables = check_tables(root, final, frozen)
    markdown = [root / "README.md", root / "AGENTS.md"]
    for directory in ["research", "report", "docs", "tests", "tools"]:
        markdown += list((root / directory).rglob("*.md"))
    links = check_links(root, markdown)
    if local_artifacts:
        for spec in frozen["models"].values():
            check_hashes(root, {spec["artifact"]: spec["sha256"]}, text=False)
        check_hashes(root / ".local_data", frozen["data_hashes"], text=False)
        check_hashes(root, {".local_data/final_evaluation_v1/final_predictions.csv": receipt["predictions_sha256"]}, text=False)
    return {"frozen_source_and_references_unchanged": True, "package_files_checked": len(manifest["files"]),
            "exact_claims_checked": claims, "local_links_checked": links, "private_hash_checks": local_artifacts,
            "aggregate_csv_tables_checked": tables,
            "raw_csv_parsed": False, "model_fitting": False, "evaluation_runs": receipt["evaluation_runs"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-artifacts", action="store_true", help="Also hash private artifacts; never parse or predict")
    args = parser.parse_args()
    print(json.dumps(verify(local_artifacts=args.local_artifacts), indent=2))


if __name__ == "__main__":
    main()
