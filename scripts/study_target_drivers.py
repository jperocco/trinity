"""Study targets and future points using supplied FP annual exports only."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from backtest_annual import load_seasons, metrics, bootstrap_delta


FEATURES=['routes_per_game','route_share','target_share','tprr','air_yard_share',
          'yard_share','yprr','redzone_targets_per_game','endzone_targets_per_game','targets_per_game','prior_ppr']
BLOCKS={
    'prior_ppr':['prior_ppr'],
    'routes_per_game':['routes_per_game'],
    'route_share':['route_share'],
    'target_share':['target_share'],
    'tprr':['tprr'],
    'yard_share':['yard_share'],
    'yprr':['yprr'],
    'targets_per_game':['targets_per_game'],
    'volume_relevance':['targets_per_game','target_share'],
    'volume_relevance_routes':['targets_per_game','target_share','routes_per_game','route_share'],
    'volume_relevance_quality':['targets_per_game','target_share','air_yard_share','redzone_targets_per_game','endzone_targets_per_game'],
    'all_opportunity':['targets_per_game','target_share','routes_per_game','route_share','tprr','air_yard_share','redzone_targets_per_game','endzone_targets_per_game'],
    'prior_ppr_plus_usage':['prior_ppr','targets_per_game','target_share','routes_per_game','route_share','tprr','air_yard_share','redzone_targets_per_game','endzone_targets_per_game'],
    'prior_ppr_plus_usage_efficiency':['prior_ppr','targets_per_game','target_share','routes_per_game','route_share','tprr','air_yard_share','redzone_targets_per_game','endzone_targets_per_game','yard_share','yprr'],
}


def main():
    frames,audit=load_seasons(Path('data/history/fantasypoints'))
    annual=pd.concat(frames.values(),ignore_index=True)
    annual['routes_per_game']=annual.RTE/annual.G
    annual['targets_per_game']=annual.TGT/annual.G
    annual['route_share']=annual['RTE %']/100
    annual['target_share']=annual['TGT %']/100
    annual['tprr']=annual.TGT/annual.RTE.replace(0,np.nan)
    annual['yprr']=annual.YDS/annual.RTE.replace(0,np.nan)
    annual['air_yard_share']=annual['AY Share']/100
    annual['yard_share']=annual['TM YDS %']/100
    annual['redzone_targets_per_game']=annual['i20 TGT']/annual.G
    annual['endzone_targets_per_game']=annual.EZTGT/annual.G
    annual['prior_ppr']=annual['FP/G']
    annual=annual[np.isfinite(annual[FEATURES]).all(axis=1)].copy()
    result={}
    for pos in ['WR','TE']:
        data=annual[annual.POS==pos]
        correlations={outcome:{feature:float(data[feature].corr(data[outcome],method='spearman')) for feature in FEATURES}
                      for outcome in ['targets_per_game','prior_ppr']}
        pairs=[]
        for year in range(2021,2025):
            prior=data[data.Season==year]
            future=data[data.Season==year+1][['identity','targets_per_game','prior_ppr']].rename(columns={'targets_per_game':'future_targets','prior_ppr':'future_ppr'})
            pair=prior.merge(future,on='identity',validate='one_to_one')
            pair['outcome_year']=year+1
            pairs.append(pair)
        pairs=pd.concat(pairs,ignore_index=True)
        train=pairs[pairs.outcome_year<=2024]
        test=pairs[pairs.outcome_year==2025]
        outcomes={}
        for outcome in ['future_targets','future_ppr']:
            predictions={}
            for name,features in BLOCKS.items():
                model=make_pipeline(StandardScaler(),Ridge(alpha=10))
                model.fit(train[features],train[outcome])
                predictions[name]=model.predict(test[features])
            y=test[outcome].to_numpy()
            outcomes[outcome]={name:dict(holdout=metrics(y,prediction),versus_prior_ppr=bootstrap_delta(y,prediction,predictions['prior_ppr'])) for name,prediction in predictions.items()}
        result[pos]=dict(annual_n=len(data),train_pairs=len(train),test_pairs=len(test),
            same_season_rank_correlations=correlations,next_season_forecasts=outcomes)
    report=dict(source='Supplied Fantasy Points 2021–2025 only; no external joins',
        method='Spearman same-season associations; standardized ridge alpha=10 fixed for every future-year model. Train outcomes 2022–2024; test outcome 2025, already inspected in previous experiments. Same complete-case sample per position for all models.',
        features=FEATURES,blocks=BLOCKS,audit=audit,positions=result,
        limitations=['Targets per game = routes per game × targets per route by definition; same-season association is not a test of sustainability.',
                     'Yard share and YPRR contain realized receiving yards, a direct component of contemporaneous fantasy scoring; use lagged values for future forecasts.',
                     'Annual future-year forecasts cannot establish optimal weekly weights. Current-year rows do not include targets yet to occur.',
                     'FP i20 targets identify red-zone location; end-zone targets describe destination. Both can overlap. Air-yard share is depth allocation, not catch probability or quarterback accuracy.',
                     'Players require eligible rows in both years; source name-position identity, survivorship, correlated features and one previously inspected test season limit inference.',
                     'Paired bootstrap intervals are conditional on 2025 players; exploratory model comparisons are not independent confirmations.'])
    Path('docs/TARGET_DRIVERS.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    for pos,d in result.items():
        print(pos,'annual',d['annual_n'],'future test',d['test_pairs'])
        print('same-season targets', {k:round(v,3) for k,v in d['same_season_rank_correlations']['targets_per_game'].items()})
        for outcome,models in d['next_season_forecasts'].items():print(outcome,{k:round(v['holdout']['mae'],3) for k,v in models.items()})


if __name__=='__main__':main()
