"""Trinity data contract: audit and aggregate canonical player-game CSVs."""
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

KEY = ['player_id', 'game_id', 'team']
COUNTS = ['routes', 'team_route_opportunities', 'targets', 'team_targets',
          'receiving_air_yards', 'team_receiving_air_yards', 'fantasy_points_ppr']
REQUIRED = KEY + ['season', 'week', 'position', 'played', 'source',
                  'routes_source', 'routes_definition'] + COUNTS

def audit(rows):
    errors, flags, seen = [], [], set()
    denominators = {}
    for index, row in enumerate(rows, 2):
        label = f'row {index}'
        missing = [c for c in REQUIRED if not str(row.get(c, '')).strip()]
        if missing:
            errors.append(f'{label}: missing {missing}')
            continue
        key = tuple(row[c] for c in KEY)
        if key in seen:
            errors.append(f'{label}: duplicate {key}')
        seen.add(key)
        if row['position'] not in ('WR', 'TE'):
            errors.append(f'{label}: position outside WR/TE')
        if row['played'] != '1':
            errors.append(f'{label}: canonical input must contain played games only')
        try:
            values = {c: float(row[c]) for c in COUNTS}
            if not all(math.isfinite(v) for v in values.values()):
                raise ValueError('nonfinite')
            if int(row['season']) < 2021 or not 1 <= int(row['week']) <= 18:
                raise ValueError('invalid regular-season period')
        except ValueError:
            errors.append(f'{label}: invalid numeric value')
            continue
        for numerator, denominator in [('routes', 'team_route_opportunities'), ('targets', 'team_targets')]:
            if values[numerator] < 0 or values[denominator] < 0 or values[numerator] > values[denominator]:
                errors.append(f'{label}: invalid {numerator}/{denominator}')
            if values[denominator] == 0:
                flags.append(f'{label}: zero {denominator}, share unavailable')
        for c in ['routes', 'team_route_opportunities', 'targets', 'team_targets']:
            if not values[c].is_integer():
                errors.append(f'{label}: {c} must be an integer count')
        air_den = values['team_receiving_air_yards']
        if air_den <= 0 or not 0 <= values['receiving_air_yards'] / air_den <= 1:
            flags.append(f'{label}: unusual air-yard denominator/share; retained')
        team_key = (row['game_id'], row['team'])
        current = tuple(values[c] for c in ['team_targets', 'team_receiving_air_yards', 'team_route_opportunities']) + (row['routes_source'], row['routes_definition'])
        if team_key in denominators and denominators[team_key] != current:
            errors.append(f'{label}: inconsistent team-game denominators or route definition')
        denominators[team_key] = current
    return {'rows': len(rows), 'errors': errors, 'flags': flags, 'passed': not errors}

def aggregate(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row['player_id'], row['season'], row['team'], row['position'])].append(row)
    result = []
    for key, games in sorted(groups.items()):
        definitions = {(g['routes_source'], g['routes_definition']) for g in games}
        if len(definitions) != 1:
            raise ValueError(f'mixed route definitions for {key}')
        totals = {c: sum(float(g[c]) for g in games) for c in COUNTS}
        item = dict(zip(['player_id', 'season', 'team', 'position'], key))
        item.update(totals)
        item['games'] = len(games)
        for name, numerator, denominator in [('route_share','routes','team_route_opportunities'), ('target_share','targets','team_targets'), ('air_yard_share','receiving_air_yards','team_receiving_air_yards')]:
            item[name] = totals[numerator] / totals[denominator] if totals[denominator] else None
        item['ppr_per_game'] = totals['fantasy_points_ppr'] / len(games)
        result.append(item)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--start-week', type=int, default=1)
    parser.add_argument('--end-week', type=int, default=18)
    args = parser.parse_args()
    if not 1 <= args.start_week <= args.end_week <= 18:
        parser.error('invalid week interval')
    with args.input.open(newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    report = audit(rows)
    if not report['passed']:
        print(json.dumps(report, indent=2))
        raise SystemExit(1)
    selected = [r for r in rows if args.start_week <= int(r['week']) <= args.end_week]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({'audit': report, 'aggregates': aggregate(selected)}, indent=2), encoding='utf-8')
    print(f'PASS: {len(selected)} player-games; {len(report["flags"])} flags; {args.output}')

if __name__ == '__main__':
    main()
