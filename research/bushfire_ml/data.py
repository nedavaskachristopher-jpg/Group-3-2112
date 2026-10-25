"""Explicit feature selection and development-only data access."""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "config" / "protocol_v1.json"
LOCAL_ROOT = ROOT / ".local_data"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_protocol(path: Path = PROTOCOL_PATH) -> dict:
    protocol = json.loads(path.read_text(encoding="utf-8"))
    excluded = set(protocol["excluded_predictors"])
    for name, columns in protocol["feature_sets"].items():
        if len(columns) != len(set(columns)) or excluded.intersection(columns):
            raise ValueError(f"Unsafe or duplicate predictors in {name}")
    return protocol


def partition_for(feature_date: str, protocol: dict) -> str:
    day = date.fromisoformat(feature_date)
    start = date.fromisoformat(protocol["feature_date_start"])
    end = date.fromisoformat(protocol["feature_date_end"])
    train_end = date.fromisoformat(protocol["original_train_end"])
    validation_end = date.fromisoformat(protocol["original_validation_end"])
    gap = timedelta(days=protocol["gap_days"])
    if not start <= day <= end:
        raise ValueError("Feature date is outside the frozen study period")
    if day <= train_end - gap:
        return "train"
    if day <= train_end:
        return "embargo"
    if day <= validation_end - gap:
        return "validation"
    if day <= validation_end:
        return "embargo"
    return "final_test"


def verify_seal(local_root: Path = LOCAL_ROOT) -> dict:
    manifest = json.loads((local_root / "seal_manifest.json").read_text(encoding="utf-8"))
    if sha256(PROTOCOL_PATH) != manifest["protocol_sha256"]:
        raise RuntimeError("The protocol changed after sealing")
    for relative, expected in manifest["file_sha256"].items():
        if sha256(local_root / relative) != expected:
            raise RuntimeError(f"Sealed file changed: {relative}")
    return manifest


def load_development(partition: str, local_root: Path = LOCAL_ROOT):
    if partition not in {"train", "validation"}:
        raise ValueError("Only train and validation are available to development code")
    import pandas as pd

    verify_seal(local_root)
    return pd.read_csv(local_root / "development" / f"{partition}.csv")


def model_matrix(frame, feature_set: str = "conditions_core"):
    """Select named inputs; numeric dtype is never a feature-selection rule."""
    protocol = read_protocol()
    if feature_set == "conditions_core":
        columns = protocol["feature_sets"]["conditions_core"]
    elif feature_set == "core_plus_fire_today":
        # Lesson 4 permits only the audited same-day flag, not the unreviewed
        # rainfall/dry-history additions. The original sealed protocol is intact.
        columns = [*protocol["feature_sets"]["conditions_core"], "fire_today"]
        if not frame["fire_today"].isin([0, 1]).all():
            raise ValueError("Current-fire input must be a binary same-day flag")
    else:
        raise ValueError("Extended features require a documented review before modelling")
    if frame[columns].isna().any().any():
        raise ValueError("Missing predictor values require training-only preprocessing")
    return frame.loc[:, columns].copy()
