"""Create nonnegative Trinity v0.1 weights from FP annual exports only.

Annual weights describe same-season production. JJ weekly results are an initial
transfer experiment, not proof that these are optimal future-week weights.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls

from backtest_annual import FEATURES, load_seasons, metrics

NAMES = ['route_share', 'target_share', 'air_yard_share']


def fit_weights(frame):
    x = frame[FEATURES].to_numpy(dtype=float) / 100
    y = frame['FP/G'].to_numpy(dtype=float)
    xm, ym = x.mean(axis=0), y.mean()
    coefficients, _ = nnls(x - xm, y - ym)
    amplitude = float(coefficients.sum())
    if amplitude <= 0:
        raise ValueError('No positive opportunity signal in this sample')
    return dict(weights=dict(zip(NAMES, (coefficients / amplitude).tolist())),
                intercept=float(ym-xm@coefficients), amplitude=amplitude, n=len(frame))


def score(shares, model):
    """Shares are ratios; return raw 100x weighted share, without clipping."""
    return np.asarray(shares) @ np.array([model['weights'][k] for k in NAMES]) * 100


def predict_annual(frame, model):
    return model['intercept'] + model['amplitude'] * score(frame[FEATURES]/100, model)/100


def annual_calibration(directory):
    frames, audit = load_seasons(directory)  # No crosswalk and no other provider.
    all_rows = pd.concat(frames.values(), ignore_index=True)
    result = {}
    for position in ['WR','TE']:
        data = all_rows[all_rows.POS==position]
        rolling = []
        for year in range(2022,2026):
            past, next_season = data[data.Season<year], data[data.Season==year]
            model = fit_weights(past)
            rolling.append(dict(test_season=year, model=model,
                same_season_holdout=metrics(next_season['FP/G'].to_numpy(),predict_annual(next_season,model)),
                comparison_target_only_spearman=float(next_season['TGT %'].corr(next_season['FP/G'],method='spearman'))))
        final = fit_weights(data)
        leave_one_out = {str(y):fit_weights(data[data.Season!=y])['weights'] for y in range(2021,2026)}
        result[position] = dict(deployment=final, rolling_season_checks=rolling,
            leave_one_season_out_weights=leave_one_out,
            leave_one_season_out_range={k:[min(v[k] for v in leave_one_out.values()),max(v[k] for v in leave_one_out.values())] for k in NAMES})
    return dict(version='0.1', source='Supplied Fantasy Points 2021–2025 only',
        objective='Minimize same-season squared FP/G error with an unconstrained intercept and nonnegative share coefficients; normalize coefficients to sum 1.',
        score_definition='100 * (w_route * route_share + w_target * target_share + w_air * air_yard_share); shares are ratios, not percent numbers.',
        interpretation='Opportunity index in weighted percentage points, not a percentile or a probability. Unclipped, so unusual source shares can place it outside 0–100.',
        audit=audit, positions=result,
        limitations=['Annual descriptive fit; no claim of optimal future-week forecasting weights.',
                     'Rolling annual checks test generalization to another season, using shares and production from that same season.',
                     'Weights have equal percentage-point input units; their percentages are not causal importance or variance explained.',
                     'Collinear shares can produce zero coefficients; no minimum positive weight is forced.',
                     'Deployment fit uses all eligible 2021–2025 rows. Earlier 2025 analyses mean this is exploratory, not a new untouched holdout.',
                     'FP and JJ are used separately; cross-provider IDs, statistics and denominators are not combined.'])


def weekly_application(csv_path, calibration, output_dir):
    data = pd.read_csv(csv_path)
    data['identity'] = data.player.astype(str)+'|'+data.team+'|'+data.position
    if data.duplicated(['identity','season','week']).any():
        raise ValueError('Multiple JJ rows for the same player-team-position-week')
    denominators = ['team_route_opportunities','team_targets','team_receiving_air_yards']
    data = data[(data[denominators] > 0).all(axis=1)].copy()
    data['route_share'] = data.routes/data.team_route_opportunities
    data['target_share'] = data.targets/data.team_targets
    data['air_yard_share'] = data.receiving_air_yards/data.team_receiving_air_yards
    data['trinity_score'] = np.nan
    for position in ['WR','TE']:
        mask = data.position==position
        data.loc[mask,'trinity_score'] = score(data.loc[mask,NAMES],calibration['positions'][position]['deployment'])
    windows=[]
    for _,group in data.groupby(['identity','season']):
        by_week={int(r.week):r for r in group.itertuples()}
        for week,current in by_week.items():
            for lookback in [1,2,3]:
                history=[by_week.get(w) for w in range(week-lookback+1,week+1)]
                future=by_week.get(week+1)
                if any(r is None for r in history) or future is None:
                    continue
                shares=[sum(getattr(r,n) for r in history)/sum(getattr(r,d) for r in history)
                        for n,d in zip(['routes','targets','receiving_air_yards'],denominators)]
                model=calibration['positions'][current.position]['deployment']
                windows.append(dict(position=current.position, week=week, lookback=lookback,
                    score=float(score(shares,model)), route_share=shares[0],target_share=shares[1],air_yard_share=shares[2],
                    prior_ppr=float(np.mean([r.fantasy_points_ppr for r in history])),future_ppr=future.fantasy_points_ppr))
    observations=pd.DataFrame(windows)
    checks=[]
    for (position,lookback),group in observations.groupby(['position','lookback']):
        correlations={col:float(group[col].corr(group.future_ppr,method='spearman'))
                      for col in ['score','route_share','target_share','air_yard_share','prior_ppr']}
        per_origin={str(w):dict(n=len(g),score_spearman=float(g.score.corr(g.future_ppr,method='spearman')))
                    for w,g in group.groupby('week')}
        checks.append(dict(position=position,lookback=int(lookback),n=len(group),next_week_spearman=correlations,by_origin_week=per_origin))
    weekly_candidates={}
    for position in ['WR','TE']:
        sample=observations[(observations.position==position)&(observations.lookback==1)]
        train=sample[sample.week<=2]
        holdout=sample[sample.week==3]
        candidates=[]
        for route in range(21):
            for target in range(21-route):
                weights=np.array([route,target,20-route-target])/20
                train_score=train[NAMES].to_numpy()@weights
                rho=float(pd.Series(train_score).corr(pd.Series(train.future_ppr.to_numpy()),method='spearman'))
                candidates.append((rho,weights))
        rho,weights=max(candidates,key=lambda x:x[0])
        holdout_score=holdout[NAMES].to_numpy()@weights
        holdout_rho=float(pd.Series(holdout_score).corr(pd.Series(holdout.future_ppr.to_numpy()),method='spearman'))
        weekly_candidates[position]=dict(weights=dict(zip(NAMES,weights.tolist())),train_origins=[1,2],test_origin=3,
            train_n=len(train),test_n=len(holdout),train_spearman=rho,test_spearman=holdout_rho,
            test_baselines={col:float(holdout[col].corr(holdout.future_ppr,method='spearman'))
                            for col in ['score','route_share','target_share','air_yard_share','prior_ppr']})
        mask=data.position==position
        data.loc[mask,'weekly_candidate_score']=data.loc[mask,NAMES].to_numpy()@weights*100
    output_dir.mkdir(parents=True,exist_ok=True)
    data.to_csv(output_dir/'jj_trinity_v01_weekly.csv',index=False)
    observations.to_csv(output_dir/'jj_trinity_v01_forward.csv',index=False)
    return dict(source='JJ Stats canonical inclusive uploaded 2026 snapshot only', input_rows=len(pd.read_csv(csv_path)),
        scored_rows=len(data), weeks=sorted(int(w) for w in data.week.unique()), initial_forward_checks=checks,
        weekly_candidates=weekly_candidates,
        weekly_candidate_method='Exploratory 5-percentage-point simplex grid maximizing next-week rank correlation on origins 1 and 2, tested on origin 3. This split was chosen after inspecting annual-weight weekly summaries; not a pristine holdout. No tuning on origin-3 outcomes within grid search. Candidate score stays separate from annual score. Only three transitions; no ideal-weight claim.',
        note='Weights fixed from annual FP calibration; no fitting on JJ outcomes. Consecutive observed calendar weeks required; missing games are not zero-filled. Windows use ratios of summed numerators/denominators. Repeated players and overlapping windows make observations dependent; no significance claim. JJ player-game outputs stay local.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fp-dir',type=Path,default=Path('data/history/fantasypoints'))
    p.add_argument('--jj-csv',type=Path,default=Path('data/raw/jj/canonical_inclusive_2026.csv'))
    p.add_argument('--local-output',type=Path,default=Path('data/processed/trinity_v01'))
    p.add_argument('--report',type=Path,default=Path('docs/TRINITY_V01_CALIBRATION.json'))
    args=p.parse_args()
    report=annual_calibration(args.fp_dir)
    if args.jj_csv.exists():
        report['jj_weekly']=weekly_application(args.jj_csv,report,args.local_output)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({p:v['deployment'] for p,v in report['positions'].items()},indent=2))
    print(json.dumps(report.get('jj_weekly',{}),indent=2))


if __name__=='__main__':
    main()
