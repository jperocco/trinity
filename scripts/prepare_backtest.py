"""Build strictly forward calendar-week samples from audited canonical data."""
import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trinity import audit, aggregate

def samples(rows, lookback=3, horizon=3, allow_local=False):
    report = audit(rows)
    if not report['passed']:
        raise ValueError('canonical audit failed')
    if lookback < 1 or horizon < 1:
        raise ValueError('windows must be positive')
    groups = defaultdict(dict)
    for row in rows:
        if not allow_local and row['player_id'].startswith('jj-local:'):
            continue
        key = (row['player_id'], row['season'], row['team'], row['position'])
        week = int(row['week'])
        if week in groups[key]:
            raise ValueError('duplicate player-team calendar week')
        groups[key][week] = row
    result = []
    for key, weeks in sorted(groups.items()):
        for cutoff in sorted(weeks):
            before = list(range(cutoff-lookback+1, cutoff+1))
            after = list(range(cutoff+1, cutoff+horizon+1))
            # Complete-case experiment only: bye/inactive/missing not treated as zero.
            if not all(w in weeks for w in before+after):
                continue
            past = aggregate([weeks[w] for w in before])[0]
            future = [weeks[w] for w in after]
            features = {c:past[c] for c in ['route_share','target_share','air_yard_share','ppr_per_game']}
            if any(v is None for v in features.values()):
                continue
            result.append(dict(player_id=key[0], season=int(key[1]), team=key[2], position=key[3],
                feature_start_week=before[0], cutoff_week=cutoff, target_end_week=after[-1],
                **features, future_ppr_per_game=sum(float(r['fantasy_points_ppr']) for r in future)/horizon))
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--lookback',type=int,default=3)
    p.add_argument('--horizon',type=int,default=3)
    args=p.parse_args()
    with args.input.open(newline='') as f: rows=list(csv.DictReader(f))
    result=samples(rows,args.lookback,args.horizon)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'samples':result,'limitations':[
        'Complete observed windows only; inactive/bye/missing games excluded, creating selection bias.',
        'Calendar weeks, not team-game sequence. Schedule-aware version required for primary experiment.',
        'Provisional local IDs excluded. No model fitted and no predictive validity claimed.',
        'Train/test split must purge overlapping outcome windows before any fitting.'
    ]},indent=2))
    print(f'{len(result)} forward samples; lookback={args.lookback}; horizon={args.horizon}')

if __name__=='__main__':main()
