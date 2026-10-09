"""Frozen annual model versus future weekly JJ points; no weight tuning."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from backtest_annual import metrics
from build_weekly_view import build_rows
from evaluate_feature_expansion import clustered_delta


def forward_pairs(rows):
    """Require actual observations in adjacent calendar weeks; never fill absences."""
    observed = rows[rows.has_observation].copy()
    future = observed[['identity', 'week', 'ppr']].rename(columns={'ppr': 'future_ppr'})
    future['week'] -= 1
    return observed.merge(future, on=['identity', 'week'], validate='one_to_one')


def main():
    source = pd.read_csv('data/raw/jj/canonical_inclusive_2026.csv')
    legacy = json.loads(Path('models/trinity_weekly_v01.json').read_text())['positions']
    frozen = json.loads(Path('models/trinity_points_v02.json').read_text())
    rows = pd.DataFrame(build_rows(source, legacy, frozen['positions']))
    pairs = forward_pairs(rows)
    forecasts = {'score_consolidated': 'cumulative_points_reference', 'score_last_week': 'points_reference',
                 'ppr_consolidated': 'cumulative_ppr', 'ppr_last_week': 'ppr'}
    rank_only = {'targets_consolidated': 'cumulative_targets_per_game', 'targets_last_week': 'targets_per_game'}
    results = {}
    for pos in ['WR', 'TE']:
        sample = pairs[pairs.position == pos].copy()
        # Bootstrap identity groups preserve within-player dependence across origins.
        sample['score_consolidated'] = sample.cumulative_points_reference
        sample['ppr_consolidated'] = sample.cumulative_ppr
        summary = {name: metrics(sample.future_ppr.to_numpy(), sample[column].to_numpy()) for name, column in forecasts.items()}
        ranks = {name: float(sample[column].corr(sample.future_ppr, method='spearman')) for name, column in rank_only.items()}
        folds = {}
        for week, fold in sample.groupby('week'):
            folds[str(int(week))] = {'n': len(fold), 'forecasts': {name: metrics(fold.future_ppr.to_numpy(), fold[column].to_numpy()) for name, column in forecasts.items()},
                'target_rank_correlations': {name: float(fold[column].corr(fold.future_ppr, method='spearman')) for name, column in rank_only.items()}}
        eligible = rows[(rows.position == pos) & rows.has_observation & (rows.week < rows.week.max())]
        results[pos] = {'pairs': len(sample), 'players': sample.identity.nunique(), 'eligible_origin_rows': len(eligible),
            'origins_without_next_observation': len(eligible) - len(sample), 'summary': summary, 'target_rank_correlations': ranks,
            'score_vs_ppr_consolidated': clustered_delta(sample, 'score_consolidated', 'ppr_consolidated'), 'folds': folds}
    report = {'source': 'JJ canonical inclusive 2026 only; source archive unchanged', 'model_version': frozen['version'],
        'method': 'Frozen FP annual-trained equation, no JJ fitting or weight selection. Cutoffs 1,2,3 predict observed PPR in calendar weeks 2,3,4. Consolidated inputs use only records at or before cutoff. Identical adjacent-observation sample for all comparisons. MAE compares annual-equivalent points reference with weekly PPR; 0–10 score itself is not in PPR units. Targets evaluated by rank correlation only, not a points conversion.',
        'positions': results, 'limitations': ['Only three prediction origins, conditional on players with observed rows in both adjacent weeks; missing rows are not zeros.',
            'Annual-trained model has not been calibrated for weekly outcomes. Current JJ archive is retrospective, not a real-time historical snapshot.',
            'Player-cluster bootstrap does not capture team/game dependence or season-to-season uncertainty.',
            'Pooled rank correlations mix prediction weeks; per-origin results are also reported.',
            'This is exploratory: JJ weeks have been inspected in prior work. No coefficients or UI changed.']}
    Path('docs/WEEKLY_POINTS_EVALUATION.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    lines = ['# Validação semanal do score congelado', '', report['method'], '', '| Posição | Modelo | MAE PPR | Spearman |', '|---|---|---:|---:|']
    for pos, r in results.items():
        for name, m in r['summary'].items():
            lines.append(f"| {pos} | {name} | {m['mae']:.3f} | {m['spearman']:.3f} |")
        for name, value in r['target_rank_correlations'].items():
            lines.append(f'| {pos} | {name} | — | {value:.3f} |')
    lines += ['', '## Cortes cronológicos', '', '| Posição | Corte → semana prevista | N | MAE score consolidado | MAE PPR consolidado |', '|---|---|---:|---:|---:|']
    for pos, r in results.items():
        for week, f in r['folds'].items():
            lines.append(f"| {pos} | 1–{week} → {int(week)+1} | {f['n']} | {f['forecasts']['score_consolidated']['mae']:.3f} | {f['forecasts']['ppr_consolidated']['mae']:.3f} |")
    lines += ['', '## Incerteza e cobertura', '']
    for pos, r in results.items():
        delta = r['score_vs_ppr_consolidated']
        lines.append(f"- {pos}: {r['pairs']} pares, {r['players']} jogadores; {r['origins_without_next_observation']} de {r['eligible_origin_rows']} observações de origem sem registro na semana seguinte. Δ MAE score − PPR consolidado: {delta['delta_mae']:+.3f}, IC95% [{delta['ci95'][0]:+.3f}, {delta['ci95'][1]:+.3f}].")
    lines += ['', '## Limitações', ''] + ['- ' + s for s in report['limitations']]
    Path('docs/WEEKLY_POINTS_EVALUATION.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
