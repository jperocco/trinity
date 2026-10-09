"""Audit locally downloaded nflverse stats; no inferred routes or games played."""
import csv
import hashlib
import json
from pathlib import Path

reports = []
for path in sorted(Path('data/raw/nflverse').glob('player_stats_*.csv')):
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        rows = list(reader)
    regular = [r for r in rows if r['season_type'] == 'REG']
    receivers = [r for r in regular if r['position'] in ('WR', 'TE')]
    keys = [(r['player_id'], r['season'], r['week']) for r in receivers]
    fields = ['targets', 'receiving_air_yards', 'fantasy_points_ppr']
    reports.append(dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        total_rows=len(rows), wr_te_regular_rows=len(receivers),
        wr_rows=sum(r['position']=='WR' for r in receivers), te_rows=sum(r['position']=='TE' for r in receivers),
        weeks=sorted({int(r['week']) for r in regular}), duplicate_player_weeks=len(keys)-len(set(keys)),
        missing={c:sum(r.get(c,'')=='' for r in receivers) for c in fields},
        has_routes='routes' in columns, columns=columns))
output = Path('docs/NFLVERSE_AUDIT.json')
output.write_text(json.dumps({'files':reports,'limitations':[
    'Rows with statistics are not a complete played-game ledger; zero-stat games may be absent.',
    'No routes or compatible route denominator; not ready for score training.',
    'Team totals must include all positions before filtering WR/TE.',
    'Coverage in these legacy assets does not establish coverage in newer endpoints.'
]}, indent=2), encoding='utf-8')
print(output)
