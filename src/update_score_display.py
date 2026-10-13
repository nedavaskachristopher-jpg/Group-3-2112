"""Refresh display columns in stored predictions without retraining models."""
import pandas as pd
from audit_data import ROOT
from predict import predict_frame
from score_display import add_score_percentages


def main():
    path = ROOT / 'output/results/predictions.csv'
    predictions = pd.read_csv(path)
    updated = add_score_percentages(predictions, score_column='score')
    updated.to_csv(path, index=False)
    features = pd.read_csv(ROOT / 'output/example_features.csv')
    example = predict_frame(features, ROOT / 'output/models/chronological_xgb_full.json')
    example.to_csv(ROOT / 'output/example_scores.csv', index=False)
    print(f'Added percentage displays to {len(updated)} stored prediction rows and {len(example)} inference examples. No models were retrained.')


if __name__ == '__main__':
    main()
