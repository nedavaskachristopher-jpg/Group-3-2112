"""Small model-fitting functions; experiment runners own data selection."""

import warnings

import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data import model_matrix


def fit_logistic(training: pd.DataFrame, config: dict) -> Pipeline:
    """Fit preprocessing and logistic weights on training observations only."""
    predictors = model_matrix(training, config["feature_set"])
    labels = training.fire_positive.astype(int)
    if set(labels.unique()) != {0, 1}:
        raise ValueError("Both classes must occur in the training partition")
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(**config["logistic_regression"])),
    ])
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        pipeline.fit(predictors, labels)
    return pipeline


def fit_xgboost(training: pd.DataFrame, validation: pd.DataFrame, config: dict, feature_set: str):
    """Fit shallow boosted trees; validation selects boosting length only."""
    from sklearn.metrics import average_precision_score
    from xgboost import XGBClassifier
    from xgboost.callback import EarlyStopping

    if not pd.to_datetime(training.target_date).max() < pd.to_datetime(validation.feature_date).min():
        raise ValueError("Training outcomes must precede validation feature dates")
    labels = training.fire_positive.astype(int)
    if set(labels.unique()) != {0, 1} or set(validation.fire_positive.unique()) != {0, 1}:
        raise ValueError("Both classes are needed in training and early-stopping data")
    train_x = model_matrix(training, feature_set)
    validation_x = model_matrix(validation, feature_set)
    stopping = config["early_stopping"]
    if stopping["metric"] != "average_precision_score" or not stopping["maximize"]:
        raise ValueError("Early stopping must maximise the reported AP definition")
    callback = EarlyStopping(rounds=stopping["rounds"], metric_name="average_precision_score",
                             data_name="validation_1", maximize=True, save_best=stopping["save_best"])
    model = XGBClassifier(**config["xgboost"], eval_metric=average_precision_score,
                          scale_pos_weight=float(labels.eq(0).sum()/labels.eq(1).sum()),
                          callbacks=[callback])
    model.fit(train_x, labels, eval_set=[(train_x, labels), (validation_x, validation.fire_positive)], verbose=False)
    return model


def fit_xgboost_fixed(training: pd.DataFrame, config: dict, feature_set: str, tree_count: int):
    """Refit a past-selected tree count without an evaluation set or callbacks."""
    from xgboost import XGBClassifier

    if not isinstance(tree_count, int) or not 1 <= tree_count <= config["xgboost"]["n_estimators"]:
        raise ValueError("Tree count must be within the configured fitting budget")
    labels = training.fire_positive.astype(int)
    if set(labels.unique()) != {0, 1}:
        raise ValueError("Both classes are needed in refitting data")
    parameters = dict(config["xgboost"], n_estimators=tree_count)
    model = XGBClassifier(**parameters,
                          scale_pos_weight=float(labels.eq(0).sum()/labels.eq(1).sum()))
    model.fit(model_matrix(training, feature_set), labels, verbose=False)
    return model
