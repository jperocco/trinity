"""Expanding-year evaluation of supplied annual FP data; no external joins."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from backtest_annual import load_seasons, metrics
from train_points_model import fit

CORE = ['targets_per_game', 'target_share']
BLOCKS = {
    'core': CORE,
    'efficiency': CORE + ['yprr', 'yard_share'],
    'quality': CORE + ['air_yard_share', 'redzone_targets_per_game', 'endzone_targets_per_game'],
    'full': CORE + ['yprr', 'yard_share', 'air_yard_share', 'redzone_targets_per_game', 'endzone_targets_per_game', 'routes_per_game', 'route_share'],
    'prior_ppr': ['prior_ppr'],
}


def chronological_split(pairs, year):
    train = pairs[pairs.outcome_year < year]
    test = pairs[pairs.outcome_year == year]
    if train.empty or test.empty:
        raise ValueError('Empty chronological fold')
    return train, test


def clustered_delta(rows, candidate, baseline):
    delta = np.abs(rows[candidate] - rows.future_ppr) - np.abs(rows[baseline] - rows.future_ppr)
    grouped = pd.DataFrame({'identity': rows.identity, 'delta': delta}).groupby('identity').delta.agg(['sum', 'count'])
    rng = np.random.default_rng(20261009)
    indices = rng.integers(len(grouped), size=(5000, len(grouped)))
    draws = grouped['sum'].to_numpy()[indices].sum(axis=1) / grouped['count'].to_numpy()[indices].sum(axis=1)
    return {'delta_mae': float(delta.mean()), 'ci95': np.quantile(draws, [.025, .975]).tolist(), 'player_clusters': len(grouped)}


def main():
    frames, audit = load_seasons(Path('data/history/fantasypoints'))
    data = pd.concat(frames.values(), ignore_index=True)
    for name, source in [('targets_per_game', 'TGT'), ('routes_per_game', 'RTE'), ('redzone_targets_per_game', 'i20 TGT'), ('endzone_targets_per_game', 'EZTGT')]:
        data[name] = data[source] / data.G
    for name, source in [('target_share', 'TGT %'), ('route_share', 'RTE %'), ('air_yard_share', 'AY Share'), ('yard_share', 'TM YDS %')]:
        data[name] = data[source] / 100
    data['yprr'] = data.YDS / data.RTE.replace(0, np.nan)
    data['prior_ppr'] = data['FP/G']
    features = sorted({f for block in BLOCKS.values() for f in block})
    data = data[np.isfinite(data[features]).all(axis=1)].copy()
    results = {}
    for position in ['WR', 'TE']:
        d = data[data.POS == position]
        pairs = []
        for year in range(2021, 2025):
            future = d[d.Season == year + 1][['identity', 'prior_ppr']].rename(columns={'prior_ppr': 'future_ppr'})
            pair = d[d.Season == year].merge(future, on='identity', validate='one_to_one')
            pair['outcome_year'] = year + 1
            pairs.append(pair)
        pairs = pd.concat(pairs, ignore_index=True)
        folds, predictions = {}, []
        for year in [2023, 2024, 2025]:
            train, test = chronological_split(pairs, year)
            output = test[['identity', 'outcome_year', 'future_ppr']].copy()
            for name, block in BLOCKS.items():
                output[name] = np.maximum(0, fit(train, block).predict(test[block]))
            predictions.append(output)
            folds[str(year)] = {'train_n': len(train), 'test_n': len(test), 'models': {name: metrics(output.future_ppr.to_numpy(), output[name].to_numpy()) for name in BLOCKS}}
        pooled = pd.concat(predictions, ignore_index=True)
        summary = {}
        for name in BLOCKS:
            summary[name] = {'pooled': metrics(pooled.future_ppr.to_numpy(), pooled[name].to_numpy()),
                'versus_core': clustered_delta(pooled, name, 'core'),
                'versus_prior_ppr': clustered_delta(pooled, name, 'prior_ppr'),
                'folds_better_than_core': sum(f['models'][name]['mae'] < f['models']['core']['mae'] for f in folds.values())}
        results[position] = {'annual_n': len(d), 'folds': folds, 'summary': summary}
    report = {'source': 'Supplied FP 2021–2025 only; exact same-provider name and position; no external joins',
        'method': 'Same complete-case sample for every model, six-plus games in both seasons. StandardScaler + Ridge alpha=10 fixed, fitted only on outcome years before each test year. Outcomes 2023, 2024, 2025; features always from previous season. Predictions clipped at zero. Prior-PPR comparator is a fitted one-feature ridge, not raw persistence.',
        'blocks': BLOCKS, 'audit': audit, 'positions': results,
        'limitations': ['Exploratory: 2025 and earlier results have already been inspected; these are not untouched holdouts.', 'Annual next-season predictions do not validate next-week predictions or weekly weights.', 'Bootstrap resamples player identities together across folds; intervals are conditional on these three seasons, not uncertainty over future seasons.', 'Eligibility in both years introduces survivorship; source identity is provisional.', 'YPRR uses source YDS/RTE, shares use source percentages, and red-zone/end-zone counts can overlap.', 'JJ lacks complete quality inputs; no missing values are replaced by zero.']}
    Path('docs/FEATURE_EXPANSION.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    lines = ['# Expansão de features: previsão de PPR futuro', '', report['method'], '', 'Todas as métricas abaixo são MAE em PPR/jogo; menor é melhor. Pooled pondera cada observação igualmente.', '', '| Posição | Modelo | 2023 | 2024 | 2025 | Pooled | Ganhos vs core | Δ vs core (IC95%) |', '|---|---|---:|---:|---:|---:|---:|---|']
    for pos, r in results.items():
        for name, s in r['summary'].items():
            values = [r['folds'][str(y)]['models'][name]['mae'] for y in [2023, 2024, 2025]]
            delta = s['versus_core']
            lines.append(f"| {pos} | {name} | " + ' | '.join(f'{v:.3f}' for v in values) + f" | {s['pooled']['mae']:.3f} | {s['folds_better_than_core']}/3 | {delta['delta_mae']:+.3f} [{delta['ci95'][0]:+.3f}, {delta['ci95'][1]:+.3f}] |")
    lines += ['', '## Composição dos modelos', '']
    lines += [f'- **{name}**: ' + ', '.join(block) for name, block in BLOCKS.items()]
    lines += ['', '## Limitações', ''] + ['- ' + s for s in report['limitations']]
    Path('docs/FEATURE_EXPANSION.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
