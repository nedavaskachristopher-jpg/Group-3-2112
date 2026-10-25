"""Copy date-defined partitions without inspecting holdout outcomes."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .data import LOCAL_ROOT, PROTOCOL_PATH, ROOT, partition_for, read_protocol, sha256, verify_seal


def prepare(dataset_root: Path, local_root: Path = LOCAL_ROOT) -> dict:
    dataset_root = dataset_root.resolve()
    protocol = read_protocol()
    source = dataset_root / "model_ready" / protocol["source_table"]
    if not source.is_file():
        raise FileNotFoundError("The supplied dataset root must contain model_ready")
    if local_root.exists():
        manifest = verify_seal(local_root)
        if sha256(source) != manifest["source_table_sha256"]:
            raise RuntimeError("The source table changed; the existing holdout is preserved")
        print("Existing partition seal verified. No files were overwritten.")
        return manifest

    inventory = [
        {"path": p.relative_to(dataset_root).as_posix(), "bytes": p.stat().st_size,
         "sha256": sha256(p)}
        for p in sorted(dataset_root.rglob("*")) if p.is_file()
    ]
    supplied = json.loads((dataset_root / "model_ready" / "provenance.json").read_text())
    provenance_checks = []
    for entry in supplied["sources"]:
        path = dataset_root / Path(entry["relative_path"].replace("\\", "/"))
        passed = path.is_file() and path.stat().st_size == entry["bytes"] and sha256(path) == entry["sha256"]
        provenance_checks.append({"path": path.relative_to(dataset_root).as_posix(), "passed": passed})
    if not all(item["passed"] for item in provenance_checks):
        raise ValueError("Source provenance verification failed")

    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        raise ValueError("The model table has no header")
    required = set(protocol["feature_sets"]["full"]) | {
        "grid_id", "feature_date", "target_date", "park_area_fraction", "fire_positive",
        "latitude", "longitude", "rain_history_days",
    }
    if not required.issubset(fieldnames):
        raise ValueError("Required model-table fields are absent")

    # Only keys, dates and static geography are inspected across the whole panel.
    keys = set()
    grid_dates = {}
    eligible_rows = []
    counts = Counter()
    split_dates = {}
    for row in rows:
        feature_day = date.fromisoformat(row["feature_date"])
        if date.fromisoformat(row["target_date"]) - feature_day != timedelta(days=1):
            raise ValueError("Target date is not the next UTC day")
        key = (row["grid_id"], row["feature_date"])
        if key in keys:
            raise ValueError("Duplicate grid-cell/feature-date key")
        keys.add(key)
        grid_dates.setdefault(row["grid_id"], set()).add(feature_day)
        area = float(row["park_area_fraction"])
        if not 0 <= area <= 1:
            raise ValueError("Invalid static park overlap")
        partition = partition_for(row["feature_date"], protocol)
        if area < protocol["minimum_park_area_fraction"]:
            continue
        eligible_rows.append((partition, row))
        counts[partition] += 1
        split_dates.setdefault(partition, []).append(row["feature_date"])
    start = date.fromisoformat(protocol["feature_date_start"])
    end = date.fromisoformat(protocol["feature_date_end"])
    expected_days = {start + timedelta(days=i) for i in range((end-start).days+1)}
    if any(days != expected_days for days in grid_dates.values()):
        raise ValueError("Incomplete or unexpected grid-day coverage")
    if set(counts) != {"train", "validation", "embargo", "final_test"}:
        raise ValueError("One or more frozen partitions are empty")

    developer_columns = [
        "grid_id", "feature_date", "target_date", "latitude", "longitude",
        "park_area_fraction", "rain_history_days",
        *protocol["feature_sets"]["full"], "fire_positive",
    ]
    local_root.mkdir(parents=True, exist_ok=False)
    (local_root / "development").mkdir()
    (local_root / "holdout").mkdir()
    outputs = {}
    for name in ["train", "validation", "final_test"]:
        relative = "holdout/final_test.csv" if name == "final_test" else f"development/{name}.csv"
        path = local_root / relative
        columns = fieldnames if name == "final_test" else developer_columns
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
            writer.writeheader()
            for partition, row in eligible_rows:
                if partition == name:
                    writer.writerow(row)
        outputs[relative] = sha256(path)

    manifest = {
        "protocol_version": protocol["protocol_version"],
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_sha256": sha256(PROTOCOL_PATH),
        "source_table_sha256": sha256(source),
        "source_rows": len(rows), "source_columns": len(fieldnames),
        "source_grid_cells": len(grid_dates),
        "retained_grid_cells": len({r["grid_id"] for _, r in eligible_rows}),
        "removed_edge_rows": len(rows)-len(eligible_rows),
        "partitions": {name: {"rows": counts[name], "first_feature_date": min(days),
                              "last_feature_date": max(days)}
                       for name, days in split_dates.items()},
        "file_sha256": outputs,
        "holdout_labels_profiled": False,
        "holdout_evaluated": False,
        "prior_information": protocol["prior_information"],
        "source_provenance_checks_passed": len(provenance_checks),
    }
    (local_root / "seal_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    (local_root / "source_inventory.json").write_text(json.dumps(inventory, indent=2)+"\n", encoding="utf-8")
    (local_root / "source_location.json").write_text(json.dumps({"dataset_root": str(dataset_root)}, indent=2)+"\n", encoding="utf-8")
    report_dir = ROOT / "reports"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "partition_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    verify_seal(local_root)
    print(json.dumps({"partitions": manifest["partitions"], "holdout_evaluated": False}, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", required=True, type=Path)
    args = parser.parse_args()
    prepare(args.dataset_root)


if __name__ == "__main__":
    main()
