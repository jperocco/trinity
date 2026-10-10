"""Separate public weekly experiment, receiving PPR only, no FP/JJ joins."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from backtest_annual import metrics
from evaluate_feature_expansion import clustered_delta

CORE = ['cum_targets', 'cum_ts']
OPPORTUNITY = CORE + ['recent_targets', 'recent_ts', 'cum_team_targets', 'recent_team_targets', 'cum_ays', 'recent_ays', 'cum_adot', 'games']


def build_samples(data):
    keys = ['player_id', 'season', 'posteam']
    if data.duplicated(keys + ['week']).any():
        raise ValueError('Duplicate player-team-week')
    samples = []
    for key, group in data.groupby(keys):
        group = group.sort_values('week')
        by_week = {int(r.week): r for r in group.itertuples()}
        for row in group.itertuples():
            cutoff = int(row.week)
            history = group[group.week <= cutoff]
            if len(history) < 3 or cutoff + 1 not in by_week:
                continue
            recent = history[history.week >= cutoff - 2]
            features = {}
            for prefix, h in [('cum', history), ('recent', recent)]:
                tg, team = h.rec_attempt.sum(), h.rec_attempt_team.sum()
                air, team_air = h.rec_air_yards.sum(), h.rec_air_yards_team.sum()
                features.update({prefix+'_targets': tg/len(h), prefix+'_ts': tg/team if team > 0 else np.nan,
                    prefix+'_team_targets': team/len(h), prefix+'_ays': air/team_air if team_air > 0 else np.nan,
                    prefix+'_adot': air/tg if tg > 0 else 0., prefix+'_ppr': h.ppr.mean(), prefix+'_xfp': h.xfp.mean()})
            future = by_week[cutoff+1]
            features.update(identity=key[0], season=int(key[1]), week=cutoff, position=row.position, games=len(history),
                future_targets=future.rec_attempt, future_ppr=future.ppr, last_targets=row.rec_attempt, last_ppr=row.ppr)
            samples.append(features)
    result = pd.DataFrame(samples)
    if result.empty:
        return result
    required = OPPORTUNITY + ['cum_ppr', 'cum_xfp', 'recent_xfp', 'future_targets', 'future_ppr']
    return result[np.isfinite(result[required]).all(axis=1)].copy()


def predict(train, test, features, outcome):
    model = make_pipeline(StandardScaler(), Ridge(alpha=10))
    model.fit(train[features], train[outcome])
    return np.maximum(0, model.predict(test[features]))


def main():
    frames, manifest = [], []
    for year in range(2021, 2026):
        path = Path(f'data/research/ffopportunity/ep_weekly_{year}.csv')
        frame = pd.read_csv(path, low_memory=False)
        manifest.append({'season': year, 'rows': len(frame), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'url': f'https://github.com/ffverse/ffopportunity/releases/download/v1.0.0-data/ep_weekly_{year}.csv'})
        frame = frame[(frame.week <= 18) & frame.position.isin(['WR', 'TE']) & frame.player_id.notna()].copy()
        # Explicit receiving-only scoring keeps opportunity conversion units consistent.
        frame['ppr'] = frame.receptions + .1*frame.rec_yards_gained + 6*frame.rec_touchdown + 2*frame.rec_two_point_conv - 2*frame.rec_fumble_lost
        frame['xfp'] = frame.receptions_exp + .1*frame.rec_yards_gained_exp + 6*frame.rec_touchdown_exp + 2*frame.rec_two_point_conv_exp
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True)
    samples = build_samples(data)
    report = {'source': 'ffopportunity v1.0.0 weekly, based on public nflverse play-by-play; separate from premium FP and JJ',
        'manifest': manifest, 'method': 'No refitting of upstream XFP model (documented training 2006–2020). Our standardized ridge alpha=10 fixed. Test seasons 2023,2024,2025, trained only on earlier seasons. Within-season features through cutoff; minimum 3 observed source games; actual adjacent-calendar-week outcome required, same player and team. Recent window is 3 calendar weeks, missing observations never zero-filled. Common complete-case sample. Outcome is receiving-only PPR, excluding rushing and return points. XFP reconstructed in same PPR units, without expected fumble penalty. Zero-target history aDOT convention =0, not a missing-field imputation.',
        'positions': {}, 'limitations': ['Conditional on source rows in both origin and future week: absence is not proof of inactivity or zero targets.',
            'No routes in these weekly tables; route-based target-earning hypothesis remains untested.',
            'Two-stage conversion uses only prior-season positional receiving points per target; not a learned target-quality model.',
            'Cluster bootstrap groups players across weeks; team/game dependence is not captured.',
            'Public historical XFP files are retrospective; train-period documentation does not guarantee historical real-time availability.',
            'Repeated candidate comparisons make this exploratory; no score or production coefficients changed.']}
    lines = ['# Pesquisa semanal: oportunidade antes de pontos', '', report['method'], '', '| Posição | Alvo | Modelo | 2023 MAE | 2024 MAE | 2025 MAE | Agregado MAE |', '|---|---|---|---:|---:|---:|---:|']
    coverage = []
    for pos in ['WR', 'TE']:
        d = samples[samples.position == pos]
        folds, outputs = {}, []
        for year in [2023, 2024, 2025]:
            train, test = d[d.season < year], d[d.season == year]
            output = test[['identity', 'future_targets', 'future_ppr']].copy()
            output['target_mean'] = test.cum_targets
            output['target_core'] = predict(train, test, CORE, 'future_targets')
            output['target_context'] = predict(train, test, OPPORTUNITY, 'future_targets')
            output['ppr_mean'] = test.cum_ppr
            output['ppr_last'] = test.last_ppr
            output['ppr_prior_fitted'] = predict(train, test, ['cum_ppr'], 'future_ppr')
            output['ppr_direct_core'] = predict(train, test, CORE, 'future_ppr')
            output['ppr_direct_context'] = predict(train, test, OPPORTUNITY, 'future_ppr')
            output['ppr_xfp_mean'] = test.cum_xfp
            output['ppr_xfp_fitted'] = predict(train, test, ['cum_xfp', 'recent_xfp'], 'future_ppr')
            past = data[(data.position == pos) & (data.season < year)]
            value = past.ppr.sum()/past.rec_attempt.sum()
            output['ppr_two_stage'] = output.target_context*value
            folds[str(year)] = {'train_n': len(train), 'test_n': len(test), 'prior_points_per_target': float(value),
                'models': {name: metrics(output.future_targets.to_numpy() if name.startswith('target_') else output.future_ppr.to_numpy(), output[name].to_numpy()) for name in output.columns if name.startswith(('target_', 'ppr_'))}}
            outputs.append(output)
        pooled = pd.concat(outputs, ignore_index=True)
        summary = {}
        for name in folds['2023']['models']:
            target = 'future_targets' if name.startswith('target_') else 'future_ppr'
            summary[name] = metrics(pooled[target].to_numpy(), pooled[name].to_numpy())
            if target == 'future_ppr':
                summary[name]['versus_fitted_ppr'] = clustered_delta(pooled, name, 'ppr_prior_fitted')
                summary[name]['versus_ppr_mean'] = clustered_delta(pooled, name, 'ppr_mean')
            vals = [folds[str(y)]['models'][name]['mae'] for y in [2023, 2024, 2025]]
            lines.append(f'| {pos} | {target} | {name} | ' + ' | '.join(f'{v:.3f}' for v in vals) + f" | {summary[name]['mae']:.3f} |")
        report['positions'][pos] = {'sample_n_all_seasons': len(d), 'evaluated_n': len(pooled), 'evaluated_players': pooled.identity.nunique(), 'folds': folds, 'summary': summary}
        best = summary['ppr_xfp_mean']['versus_ppr_mean']
        coverage.append(f"- {pos}: {len(pooled)} previsões; Δ MAE XFP médio − PPR médio {best['delta_mae']:+.3f}, IC95% [{best['ci95'][0]:+.3f}, {best['ci95'][1]:+.3f}].")
    lines += ['', '## Cobertura e incerteza', ''] + coverage
    lines += ['', '## Limitações', ''] + ['- '+x for x in report['limitations']]
    Path('docs/WEEKLY_ARCHITECTURE_RESEARCH.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    Path('docs/WEEKLY_ARCHITECTURE_RESEARCH.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
