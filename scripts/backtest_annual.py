"""Exploratory annual FP-export backtest; never substitutes for weekly validation.

Requires numpy, pandas and scikit-learn. Raw exports and predictions stay local.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ['RTE %', 'TGT %', 'AY Share']
MODELS = {
    'prior_ppr': ['FP/G'],
    'route_only': ['RTE %'],
    'target_only': ['TGT %'],
    'air_only': ['AY Share'],
    'trinity': FEATURES,
    'trinity_plus_prior_ppr': FEATURES + ['FP/G'],
}


def load_seasons(directory):
    frames, audit = {}, {}
    for year in range(2021, 2026):
        frame = pd.read_csv(directory / f'receiving_advanced_{year}.csv')
        if set(frame['Season']) != {year}:
            raise ValueError(f'Unexpected season in {year} file')
        frame = frame[frame.POS.isin(['WR', 'TE'])].copy()
        # Exact same-provider name + position is provisional identity, not a stable ID.
        frame['identity'] = frame.Name.str.strip() + '|' + frame.POS
        duplicate = frame.duplicated('identity', keep=False)
        invalid = ((frame['RTE %'] < 0) | (frame['RTE %'] > 100)
                   | (frame['TGT %'] < 0) | (frame['TGT %'] > 100)
                   | (frame['AY Share'] > 100))
        numeric = frame[['G', 'FP/G'] + FEATURES]
        missing = ~np.isfinite(numeric.to_numpy(dtype=float)).all(axis=1)
        short = frame.G < 6
        audit[str(year)] = dict(rows=len(frame), duplicate_rows=int(duplicate.sum()),
                               invalid_share_rows=int(invalid.sum()),
                               missing_rows=int(missing.sum()), short_sample_rows=int(short.sum()),
                               eligible_rows=int((~(duplicate | invalid | missing | short)).sum()))
        frames[year] = frame.loc[~(duplicate | invalid | missing | short)].copy()
    return frames, audit


def transitions(frames):
    pairs = []
    for year in range(2021, 2025):
        prior = frames[year]
        future = frames[year + 1][['identity', 'FP/G']].rename(columns={'FP/G': 'outcome'})
        merged = prior.merge(future, on='identity', validate='one_to_one')
        merged['outcome_year'] = year + 1
        pairs.append(merged)
    return pd.concat(pairs, ignore_index=True)


def metrics(y, prediction):
    error = prediction - y
    return dict(n=len(y), mae=float(np.abs(error).mean()),
                rmse=float(np.sqrt(np.square(error).mean())),
                pearson=float(pd.Series(y).corr(pd.Series(prediction))),
                spearman=float(pd.Series(y).corr(pd.Series(prediction), method='spearman')))


def bootstrap_delta(y, prediction, baseline, seed=20261009):
    # One row per player in the holdout; paired resampling preserves comparison.
    delta = np.abs(prediction - y) - np.abs(baseline - y)
    rng = np.random.default_rng(seed)
    draws = delta[rng.integers(0, len(delta), size=(5000, len(delta)))].mean(axis=1)
    return dict(delta_mae=float(delta.mean()), ci95=[float(x) for x in np.quantile(draws, [.025, .975])])


def evaluate(pairs):
    result = {}
    for position in ['ALL', 'WR', 'TE']:
        sample = pairs if position == 'ALL' else pairs[pairs.POS == position]
        train = sample[sample.outcome_year <= 2023]
        validation = sample[sample.outcome_year == 2024]
        test = sample[sample.outcome_year == 2025]
        if min(len(train), len(validation), len(test)) < 3:
            raise ValueError('Insufficient observations for temporal split')
        y = test.outcome.to_numpy()
        base = test['FP/G'].to_numpy()
        out = dict(train_n=len(train), validation_n=len(validation), test_n=len(test),
                   persistence=metrics(y, base), models={})
        predictions = {}
        for name, columns in MODELS.items():
            candidates = []
            for alpha in [.01, .1, 1, 10, 100, 1000]:
                model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
                model.fit(train[columns], train.outcome)
                mae = np.abs(model.predict(validation[columns]) - validation.outcome).mean()
                candidates.append((float(mae), alpha))
            validation_mae, alpha = min(candidates)
            # Hyperparameters chosen before looking at 2025; refit through 2024.
            fitted = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
            development = pd.concat([train, validation])
            fitted.fit(development[columns], development.outcome)
            prediction = fitted.predict(test[columns])
            predictions[name] = prediction
            scaler, ridge = fitted.steps[0][1], fitted.steps[1][1]
            out['models'][name] = dict(alpha=alpha, validation_mae=validation_mae,
                holdout=metrics(y, prediction), versus_persistence=bootstrap_delta(y, prediction, base),
                coefficients_per_source_unit=dict(zip(columns, (ridge.coef_ / scaler.scale_).tolist())))
        for name, prediction in predictions.items():
            out['models'][name]['versus_calibrated_prior_ppr'] = bootstrap_delta(y, prediction, predictions['prior_ppr'])
            out['models'][name]['versus_target_only'] = bootstrap_delta(y, prediction, predictions['target_only'])
        result[position] = out
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, default=Path('data/history/fantasypoints'))
    parser.add_argument('--report', type=Path, default=Path('docs/ANNUAL_BACKTEST.json'))
    args = parser.parse_args()
    frames, audit = load_seasons(args.input_dir)
    pairs = transitions(frames)
    report = dict(kind='exploratory annual complete-case backtest', source='Fantasy Points supplied exports',
                  qualification='At least 6 source-defined G in both years; finite features and FP/G; unique exact name+position',
                  identity='Provisional exact same-provider Name+POS; not certified stable player IDs',
                  split={'train_outcomes': [2022, 2023], 'validation_outcome': 2024, 'holdout_outcome': 2025},
                  audit=audit, matched_pairs_by_outcome_year=pairs.outcome_year.value_counts().sort_index().to_dict(),
                  unmatched_eligible_prior_by_year={str(y):len(frames[y])-int((pairs.outcome_year == y+1).sum()) for y in range(2021,2025)},
                  results=evaluate(pairs),
                  limitations=['Survivorship: excludes players without an eligible next-season row; does not predict career exits.',
                               'Annual exports: no within-season forecasting or schedule/zero-stat ledger validation.',
                               'G, FP/G and shares retain provider semantics; FP/G scoring not independently reconciled.',
                               'Shares rounded; exact denominators unavailable. Negative AY shares retained; >100 excluded and flagged.',
                               'Duplicate name-position rows excluded rather than combined using invented denominators.',
                               'One final holdout season; bootstrap CI is conditional on that season, not across-season uncertainty.',
                               'All-player model has no position control; separate WR and TE models reported.'])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'report':str(args.report), 'pairs':len(pairs), 'results':report['results']}, indent=2))


if __name__ == '__main__':
    main()
