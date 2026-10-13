"""Add percentage display columns without changing scores or alert decisions."""
import numpy as np
import pandas as pd


SCORE_INTERPRETATION = 'Uncalibrated model score; not a fire occurrence probability'


def add_score_percentages(frame, score_column='model_score', threshold_column='threshold'):
    output = frame.copy()
    for column in [score_column, threshold_column]:
        values = pd.to_numeric(output[column], errors='raise').astype(np.float64)
        if not np.isfinite(values.to_numpy()).all() or not values.between(0, 1).all():
            raise ValueError(f'{column} must contain finite values between 0 and 1.')
        output[f'{column}_percent'] = values * 100.0
    return output
