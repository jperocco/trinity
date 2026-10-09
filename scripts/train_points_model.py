"""Train v0.2 future-year FP/G models; no weekly prediction claim."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from backtest_annual import load_seasons,metrics,bootstrap_delta

BLOCKS={
    'volume_relevance':['targets_per_game','target_share'],
    'plus_routes':['targets_per_game','target_share','routes_per_game','route_share'],
    'plus_air':['targets_per_game','target_share','routes_per_game','route_share','air_yard_share'],
    'quality_research':['targets_per_game','target_share','routes_per_game','route_share','air_yard_share','redzone_targets_per_game','endzone_targets_per_game'],
    'prior_ppr':['prior_ppr'],
}
DEPLOYABLE=['volume_relevance','plus_routes','plus_air']


def fit(data,features):
    model=make_pipeline(StandardScaler(),Ridge(alpha=10))
    model.fit(data[features],data.future_ppr)
    return model


def export(model,features,anchor):
    scaler,ridge=model.steps[0][1],model.steps[1][1]
    beta=ridge.coef_/scaler.scale_
    return dict(features=features,coefficients=dict(zip(features,beta.tolist())),
        intercept=float(ridge.intercept_-scaler.mean_@beta),score_anchor_ppr=float(anchor))


def project(features,model):
    if any(k not in features or not np.isfinite(features[k]) for k in model['features']):
        raise ValueError('Missing model input; no implicit zero imputation')
    points=max(0.,model['intercept']+sum(model['coefficients'][k]*features[k] for k in model['features']))
    return points,10*(1-10**(-points/model['score_anchor_ppr']))


def main():
    frames,_=load_seasons(Path('data/history/fantasypoints'))
    data=pd.concat(frames.values(),ignore_index=True)
    for name,numerator in [('targets_per_game','TGT'),('routes_per_game','RTE'),('redzone_targets_per_game','i20 TGT'),('endzone_targets_per_game','EZTGT')]:data[name]=data[numerator]/data.G
    for name,source in [('target_share','TGT %'),('route_share','RTE %'),('air_yard_share','AY Share')]:data[name]=data[source]/100
    data['prior_ppr']=data['FP/G']
    report={};deployment={}
    for pos in ['WR','TE']:
        d=data[data.POS==pos]
        pairs=[]
        for y in range(2021,2025):
            future=d[d.Season==y+1][['identity','prior_ppr']].rename(columns={'prior_ppr':'future_ppr'})
            pair=d[d.Season==y].merge(future,on='identity',validate='one_to_one');pair['outcome_year']=y+1;pairs.append(pair)
        pairs=pd.concat(pairs,ignore_index=True)
        train=pairs[pairs.outcome_year<=2023];validation=pairs[pairs.outcome_year==2024];test=pairs[pairs.outcome_year==2025]
        validation_mae={name:float(np.abs(np.maximum(0,fit(train,features).predict(validation[features]))-validation.future_ppr).mean()) for name,features in BLOCKS.items()}
        # Simpler model wins exact ties; only inputs available in JJ are deployable.
        selected=min(DEPLOYABLE,key=lambda name:(validation_mae[name],len(BLOCKS[name])))
        development=pairs[pairs.outcome_year<=2024]
        predictions={name:np.maximum(0,fit(development,features).predict(test[features])) for name,features in BLOCKS.items()}
        evaluation={name:dict(mae_validation=validation_mae[name],test=metrics(test.future_ppr.to_numpy(),prediction),
            versus_prior_ppr=bootstrap_delta(test.future_ppr.to_numpy(),prediction,predictions['prior_ppr'])) for name,prediction in predictions.items()}
        anchor=float(d.prior_ppr.quantile(.95))
        frozen=export(fit(pairs,BLOCKS[selected]),BLOCKS[selected],anchor)
        frozen.update(selected_block=selected,training_pairs=len(pairs))
        deployment[pos]=frozen
        report[pos]=dict(train_n=len(train),validation_n=len(validation),test_n=len(test),selected=selected,candidates=evaluation)
    metadata=dict(version='0.2',status='Experimental annual-trained points reference applied to JJ; not a validated next-week PPR forecast',
        training_source='Supplied FP 2021–2025 only',alpha=10,
        score_definition='10 × (1 − 10^(−nonnegative annual-equivalent FP/G / fixed position historical p95 FP/G)); anchor maps to 9, monotonic below 10; not percentile or original DD score',
        selection='2024 validation MAE after training outcomes 2022–2023; evaluation 2025 already inspected previously; final refit uses all 2022–2025 outcome pairs',
        exclusions='Quality with red-zone/end-zone inputs tested in annual research only: JJ lacks end-zone counts and red-zone counts are incomplete (636/963). No zeros substituted.',positions=deployment)
    Path('models/trinity_points_v02.json').write_text(json.dumps(metadata,indent=2)+'\n')
    Path('docs/POINTS_V02_EVALUATION.json').write_text(json.dumps(dict(model_metadata=metadata,evaluation=report),indent=2)+'\n')
    print(json.dumps(dict(models=deployment,evaluation=report),indent=2))


if __name__=='__main__':main()
