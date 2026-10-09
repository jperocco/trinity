"""Create an offline weekly explorer using fixed v0.1 weights and JJ only."""
import argparse
import json
from pathlib import Path

import pandas as pd


def build_rows(data, models):
    data=data.copy()
    data['identity']=data.player.astype(str)+'|'+data.team+'|'+data.position+'|'+data.season.astype(str)
    if data.duplicated(['identity','week']).any():
        raise ValueError('Duplicate player-team-position-week')
    numerators=['routes','targets','receiving_air_yards']
    denominators=['team_route_opportunities','team_targets','team_receiving_air_yards']
    data=data[(data[denominators]>0).all(axis=1)].copy()
    rows=[]
    for identity,group in data.groupby('identity'):
        records={int(row.week):row for row in group.itertuples()}
        for week,row in records.items():
            weights=models[row.position]['weights']
            w=[weights[k] for k in ['route_share','target_share','air_yard_share']]
            history=[]
            for prior in range(week,week-3,-1):
                if prior not in records:break
                history.append(records[prior])
            current=[getattr(row,n)/getattr(row,d) for n,d in zip(numerators,denominators)]
            shares=[sum(getattr(r,n) for r in history)/sum(getattr(r,d) for r in history) for n,d in zip(numerators,denominators)]
            previous=records.get(week-1)
            previous_score=None if previous is None else 100*sum(weight*getattr(previous,n)/getattr(previous,d) for weight,n,d in zip(w,numerators,denominators))
            weekly_score=100*sum(weight*s for weight,s in zip(w,current))
            rows.append(dict(identity=identity,player=row.player,team=row.team,position=row.position,season=int(row.season),week=week,
                score=weekly_score,delta=None if previous_score is None else weekly_score-previous_score,
                rs=current[0]*100,ts=current[1]*100,ays=current[2]*100,ppr=float(row.fantasy_points_ppr),
                rolling_score=100*sum(weight*s for weight,s in zip(w,shares)),rolling_games=len(history),
                rolling_rs=shares[0]*100,rolling_ts=shares[1]*100,rolling_ays=shares[2]*100,
                rolling_ppr=sum(r.fantasy_points_ppr for r in history)/len(history)))
    result=pd.DataFrame(rows)
    for prefix,score_col,ppr_col in [('', 'score','ppr'),('rolling_','rolling_score','rolling_ppr')]:
        groups=result.groupby(['season','week','position'])
        usage_rank=groups[score_col].rank(pct=True,method='average')
        production_rank=groups[ppr_col].rank(pct=True,method='average')
        # Rolling labels require the complete three-calendar-week window.
        complete=pd.Series(True,index=result.index) if not prefix else result.rolling_games==3
        result[prefix+'signal']='Equilibrado'
        result.loc[complete & (usage_rank>=.75) & (production_rank<=.25),prefix+'signal']='Usage alta / PPR baixo'
        result.loc[complete & (usage_rank<=.25) & (production_rank>=.75),prefix+'signal']='PPR alto / usage baixa'
        if prefix:result.loc[~complete,prefix+'signal']='Janela incompleta'
    return json.loads(result.to_json(orient='records'))


def render(rows,models,template):
    payload=json.dumps(dict(rows=rows,models=models),ensure_ascii=False,allow_nan=False).replace('<','\\u003c')
    return template.replace('__PAYLOAD__',payload)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jj-csv',type=Path,default=Path('data/raw/jj/canonical_inclusive_2026.csv'))
    parser.add_argument('--model',type=Path,default=Path('models/trinity_weekly_v01.json'))
    parser.add_argument('--output',type=Path,default=Path('data/processed/Trinity_Weekly.html'))
    args=parser.parse_args()
    models=json.loads(args.model.read_text())['positions']
    rows=build_rows(pd.read_csv(args.jj_csv),models)
    template=(Path(__file__).resolve().parents[1]/'templates/weekly.html').read_text()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(render(rows,models,template))
    print(f'{len(rows)} player-game rows -> {args.output}')


if __name__=='__main__':main()
