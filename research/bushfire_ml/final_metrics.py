"""Validate the frozen population, predict without fitting and compute fixed metrics."""

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from .data import ROOT, model_matrix
from .evaluation import evaluate, reliability_bins

KEYS = ["grid_id", "feature_date", "target_date", "fire_positive", "fire_today"]
NAMES = {"training_prevalence": "Training prevalence", "persistence": "Persistence",
         "logistic_16": "Logistic 16", "logistic_17": "Logistic 17", "xgboost_16": "XGBoost 16", "xgboost_17": "XGBoost 17"}
POLICY_NAMES = {"recall_80_policy": "80% selection-recall policy", "recall_90_policy": "90% selection-recall policy", "persistence": "Persistence"}


def validate_population(frame, frozen):
    population = frozen["test_population"]
    dates = pd.date_range(population["first_feature_date"], population["last_feature_date"]).strftime("%Y-%m-%d")
    expected = pd.MultiIndex.from_product([frozen["grid_ids"], dates], names=["grid_id", "feature_date"])
    actual = pd.MultiIndex.from_frame(frame[["grid_id", "feature_date"]])
    if len(frame) != population["rows"] or actual.has_duplicates or set(actual) != set(expected):
        raise ValueError("Final population must exactly match every frozen grid/date pair")
    feature_dates, target_dates = pd.to_datetime(frame.feature_date), pd.to_datetime(frame.target_date)
    if not (target_dates-feature_dates).eq(pd.Timedelta(days=1)).all():
        raise ValueError("Final targets must be the next UTC day")
    if not frame.park_area_fraction.between(frozen["minimum_park_area_fraction"], 1).all():
        raise ValueError("Final geography differs from the frozen area rule")
    if not frame.fire_positive.isin([0, 1]).all() or not frame.fire_today.isin([0, 1]).all():
        raise ValueError("Binary final targets and same-day flags are required")
    for spec in frozen["models"].values():
        matrix = model_matrix(frame, spec["feature_set"])
        if list(matrix.columns) != spec["columns"] or not np.isfinite(matrix.to_numpy()).all():
            raise ValueError("Final predictors differ from the frozen finite feature matrix")


def predict_frozen(frame, frozen):
    scores = {"training_prevalence": np.full(len(frame), frozen["training_prevalence"]),
              "persistence": frame.fire_today.to_numpy(dtype=float)}
    for key, spec in frozen["models"].items():
        if key.startswith("xgboost"):
            model = XGBClassifier()
            model.load_model(ROOT / spec["artifact"])
            if model.get_booster().num_boosted_rounds() != spec["trees"]:
                raise RuntimeError("Frozen tree count changed")
        else:
            model = joblib.load(ROOT / spec["artifact"])
        if list(model.feature_names_in_) != spec["columns"]:
            raise RuntimeError("Frozen model input order changed")
        scores[key] = model.predict_proba(model_matrix(frame, spec["feature_set"]))[:, 1].astype(float)
    return scores


def population_summary(frame):
    return {"rows": len(frame), "days": int(frame.feature_date.nunique()), "grid_cells": int(frame.grid_id.nunique()),
            "first_feature_date": str(frame.feature_date.min()), "last_feature_date": str(frame.feature_date.max()),
            "first_target_date": str(frame.target_date.min()), "last_target_date": str(frame.target_date.max()),
            "positives": int(frame.fire_positive.sum()), "positive_rate": float(frame.fire_positive.mean())}


def evaluate_group(frame, scores, frozen):
    config = frozen["configuration"]
    days = int(frame.feature_date.nunique())
    metrics = {}
    for key, prediction in scores.items():
        row = evaluate(frame.fire_positive, prediction, config["diagnostic_threshold"], days, key == "persistence")
        row["observed_rate"] = float(frame.fire_positive.mean())
        row["reliability_bins"] = reliability_bins(frame.fire_positive, prediction, config["reliability_bins"])
        metrics[key] = row
    policies = {policy["name"]: evaluate(frame.fire_positive, scores[config["primary_model"]], policy["threshold"], days)
                for policy in frozen["policies"]}
    policies["persistence"] = metrics["persistence"]
    return {"population": population_summary(frame), "models": metrics, "policies": policies}


def evaluate_population(frame, scores, frozen):
    result = {"all_rows": evaluate_group(frame, scores, frozen), "no_current_detection": None}
    subset = frame.fire_today.eq(0).to_numpy()
    if subset.any():
        result["no_current_detection"] = evaluate_group(frame.loc[subset], {k: v[subset] for k, v in scores.items()}, frozen)
    return result


def final_results(frame, scores, frozen):
    months = pd.to_datetime(frame.feature_date).dt.strftime("%Y-%m")
    monthly = []
    for month in frozen["configuration"]["calendar_months"]:
        mask = months.eq(month).to_numpy()
        if not mask.any():
            raise ValueError("A prespecified final calendar month is missing")
        monthly.append({"month": month, **evaluate_population(frame.loc[mask], {k: v[mask] for k, v in scores.items()}, frozen)})
    return {**evaluate_population(frame, scores, frozen), "monthly": monthly}
