"""Create an offline weekly explorer using fixed v0.1 weights and JJ only."""
import argparse
import json
from pathlib import Path

import pandas as pd
from train_points_model import project


def build_rows(data, models, points_models=None):
    data=data.copy()
    data['identity']=data.player.astype(str)+'|'+data.team+'|'+data.position+'|'+data.season.astype(str)
    if data.duplicated(['identity','week']).any():
        raise ValueError('Duplicate player-team-position-week')
    numerators=['routes','targets','receiving_air_yards']
    denominators=['team_route_opportunities','team_targets','team_receiving_air_yards']
    # Team totals are counted once per archived team-game, including games in
    # which an individual player has no eligible row. Missing players are not zeros.
    team_games=data.groupby(['season','game_id','team','week'],as_index=False).team_targets.first()
    data=data[(data[denominators]>0).all(axis=1)].copy()
    cutoffs=sorted(int(x) for x in data.week.unique())
    rows=[]
    for identity,group in data.groupby('identity'):
        records={int(row.week):row for row in group.itertuples()}
        for week in cutoffs:
            accumulated=[r for observed,r in records.items() if observed<=week]
            if not accumulated:continue
            row=records.get(week)
            observed=row is not None
            if not observed:row=max(accumulated,key=lambda r:r.week)
            weights=models[row.position]['weights']
            w=[weights[k] for k in ['route_share','target_share','air_yard_share']]
            history=[]
            for prior in range(week,week-3,-1):
                if prior not in records:break
                history.append(records[prior])
            current=[getattr(row,n)/getattr(row,d) for n,d in zip(numerators,denominators)]
            if not history:history=[row]
            shares=[sum(getattr(r,n) for r in history)/sum(getattr(r,d) for r in history) for n,d in zip(numerators,denominators)]
            previous=records.get(week-1)
            previous_score=None if previous is None else 100*sum(weight*getattr(previous,n)/getattr(previous,d) for weight,n,d in zip(w,numerators,denominators))
            weekly_score=100*sum(weight*s for weight,s in zip(w,current))
            cumulative=[sum(getattr(r,n) for r in accumulated)/sum(getattr(r,d) for r in accumulated) for n,d in zip(numerators,denominators)]
            rows.append(dict(identity=identity,player=row.player,team=row.team,position=row.position,season=int(row.season),week=week,
                has_observation=observed,last_observed_week=max(r.week for r in accumulated),
                score=weekly_score,delta=None if previous_score is None else weekly_score-previous_score,
                rs=current[0]*100,ts=current[1]*100,ays=current[2]*100,ppr=float(row.fantasy_points_ppr),
                rolling_score=100*sum(weight*s for weight,s in zip(w,shares)),rolling_games=len(history),
                rolling_rs=shares[0]*100,rolling_ts=shares[1]*100,rolling_ays=shares[2]*100,
                rolling_ppr=sum(r.fantasy_points_ppr for r in history)/len(history) if history else None,
                cumulative_score=100*sum(weight*s for weight,s in zip(w,cumulative)),cumulative_games=len(accumulated),
                cumulative_rs=cumulative[0]*100,cumulative_ts=cumulative[1]*100,cumulative_ays=cumulative[2]*100,
                cumulative_ppr=sum(r.fantasy_points_ppr for r in accumulated)/len(accumulated),
                cumulative_ppr_total=sum(r.fantasy_points_ppr for r in accumulated)))
            if not observed:
                for field in ['score','delta','rs','ts','ays','ppr','rolling_score','rolling_rs','rolling_ts','rolling_ays']:
                    rows[-1][field]=None
            output=rows[-1]
            for prefix,period in [('',[row] if observed else []),('rolling_',history if observed else []),('cumulative_',accumulated)]:
                first_week=week if not prefix else max(1,week-2) if prefix=='rolling_' else 1
                team_period=team_games[(team_games.season==row.season)&(team_games.team==row.team)&
                    (team_games.week>=first_week)&(team_games.week<=week)]
                total_team_targets=float(team_period.team_targets.sum())
                output[prefix+'team_targets_period']=total_team_targets
                output[prefix+'team_games_period']=len(team_period)
                output[prefix+'ts_period']=100*sum(r.targets for r in period)/total_team_targets if period and total_team_targets>0 else None
                output[prefix+'targets_per_game']=sum(r.targets for r in period)/len(period) if period else None
                output[prefix+'routes_per_game']=sum(r.routes for r in period)/len(period) if period else None
                if points_models:
                    output[prefix+'legacy_score']=output[prefix+'score']
                    if period:
                        features=dict(targets_per_game=output[prefix+'targets_per_game'],target_share=output[prefix+'ts']/100,
                            routes_per_game=output[prefix+'routes_per_game'],route_share=output[prefix+'rs']/100,air_yard_share=output[prefix+'ays']/100)
                        points,new_score=project(features,points_models[row.position])
                        output[prefix+'points_reference']=points
                        output[prefix+'score']=new_score
                    else:output[prefix+'points_reference']=None
            if points_models:
                output['legacy_delta']=output['delta']
                if observed and previous is not None:
                    features=dict(targets_per_game=previous.targets,target_share=previous.targets/previous.team_targets,
                        routes_per_game=previous.routes,route_share=previous.routes/previous.team_route_opportunities,
                        air_yard_share=previous.receiving_air_yards/previous.team_receiving_air_yards)
                    _,old_score=project(features,points_models[row.position])
                    output['delta']=output['score']-old_score
    result=pd.DataFrame(rows)
    for prefix,score_col,ppr_col in [('', 'score','ppr'),('rolling_','rolling_score','rolling_ppr'),('cumulative_','cumulative_score','cumulative_ppr')]:
        groups=result.groupby(['season','week','position'])
        usage_rank=groups[score_col].rank(pct=True,method='average')
        production_rank=groups[ppr_col].rank(pct=True,method='average')
        # Rolling labels require the complete three-calendar-week window.
        complete=result.has_observation if not prefix else result.rolling_games==3 if prefix=='rolling_' else pd.Series(True,index=result.index)
        result[prefix+'signal']='Equilibrado'
        result.loc[complete & (usage_rank>=.75) & (production_rank<=.25),prefix+'signal']='Usage alta / PPR baixo'
        result.loc[complete & (usage_rank<=.25) & (production_rank>=.75),prefix+'signal']='PPR alto / usage baixa'
        if prefix:result.loc[~complete,prefix+'signal']='Janela incompleta'
    return json.loads(result.to_json(orient='records'))


def render(rows,models,template,points_model=None):
    payload=json.dumps(dict(rows=rows,models=models,points_model=points_model),ensure_ascii=False,allow_nan=False).replace('<','\\u003c')
    return template.replace('__PAYLOAD__',payload)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jj-csv',type=Path,default=Path('data/raw/jj/canonical_inclusive_2026.csv'))
    parser.add_argument('--model',type=Path,default=Path('models/trinity_weekly_v01.json'))
    parser.add_argument('--points-model',type=Path,default=Path('models/trinity_points_v02.json'))
    parser.add_argument('--output',type=Path,default=Path('data/processed/Trinity_Weekly.html'))
    args=parser.parse_args()
    models=json.loads(args.model.read_text())['positions']
    points_model=json.loads(args.points_model.read_text())
    rows=build_rows(pd.read_csv(args.jj_csv),models,points_model['positions'])
    template=(Path(__file__).resolve().parents[1]/'templates/weekly.html').read_text()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(render(rows,models,template,points_model))
    print(f'{len(rows)} player-game rows -> {args.output}')


if __name__=='__main__':main()
