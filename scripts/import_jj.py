"""Read a JJ Stats SQLite snapshot without modifying it; export audited WR/TE games."""
import argparse
import csv
import hashlib
import json
import math
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trinity import REQUIRED, audit

def retain_zero_target(row, denominator):
    """Preserve explicit zero-target games without inventing NFL IDs or PPR."""
    row = dict(row)
    if row['targets'] != 0:
        return row
    if row['receiving_air_yards'] is None:
        row['receiving_air_yards'] = 0
    if row['team_air_yards'] is None and denominator is not None:
        row['team_air_yards'] = denominator
    if row['team_air_yards'] is not None:
        row['air_yards_verified'] = 1
    if not row['player_id']:
        identity = json.dumps([row['player'], row['team'], row['position']], ensure_ascii=False)
        row['player_id'] = 'jj-local:' + hashlib.sha256(identity.encode()).hexdigest()[:20]
    row['_source'] = row.get('_source', 'JJ Stats snapshot') + '; zero-target normalization; IDs prefixed jj-local are provisional, not GSIS'
    return row

def convert(row):
    reasons = []
    if row['route_is_estimate'] or row['route_source'] != 'PFF public':
        reasons.append('routes_not_confirmed_pff')
    mapping = dict(routes='routes_run', team_route_opportunities='team_routes',
                   team_receiving_air_yards='team_air_yards')
    result = {c: row[mapping.get(c,c)] for c in REQUIRED if c not in ('played','source','routes_source','routes_definition')}
    result.update(played='1', source=row.get('_source', 'JJ Stats snapshot'), routes_source='PFF public',
                  routes_definition='JJ archived team_routes; verify against PFF pass-play convention')
    result.update(player=row['player'], route_source_url=row['route_source_url'])
    for field in REQUIRED:
        if result[field] is None or str(result[field]).strip() == '':
            reasons.append('missing_' + field)
    if row['air_yards_verified'] != 1:
        reasons.append('air_yards_not_verified')
    if reasons:
        return None, reasons
    result = {k: str(v) if v is not None else '' for k,v in result.items()}
    return result, []

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database', type=Path)
    parser.add_argument('--output', type=Path, default=Path('data/raw/jj/canonical_2026.csv'))
    parser.add_argument('--recover-air-denominators', action='store_true', help='Recover only internally consistent denominators from archived shares; not external verification')
    parser.add_argument('--retain-zero-target-games', action='store_true', help='Retain explicit zero-target games using provisional namespaced IDs; no PPR imputation')
    parser.add_argument('--report', type=Path, default=Path('docs/JJ_IMPORT_AUDIT.json'))
    args = parser.parse_args()
    con = sqlite3.connect(args.database.resolve().as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT p.* FROM player_games p JOIN games_archive g USING(game_id) WHERE p.position IN ('WR','TE') AND p.season=2026 AND upper(g.status)='FINAL'").fetchall()
    all_rows = [dict(r) for r in con.execute("SELECT * FROM player_games WHERE season=2026")]
    con.close()
    rows = [dict(r) for r in rows]
    recovered = {}
    if args.recover_air_denominators:
        groups = {}
        for r in all_rows:
            groups.setdefault((r['game_id'], r['team']), []).append(r)
        for key, group in groups.items():
            evidence = [r['receiving_air_yards']/r['air_yards_share'] for r in group
                        if r['receiving_air_yards'] is not None and r['air_yards_share'] is not None
                        and r['receiving_air_yards'] != 0 and r['air_yards_share'] != 0]
            if len(evidence) >= 2 and all(math.isfinite(v) for v in evidence):
                value = round(evidence[0])
                if value > 0 and all(abs(v-value) < 1e-6 for v in evidence):
                    recovered[key] = value
        for r in rows:
            key = (r['game_id'], r['team'])
            value = recovered.get(key)
            if r['team_air_yards'] is None and value is not None and r['receiving_air_yards'] is not None and r['air_yards_share'] is not None:
                if abs(r['receiving_air_yards']/value-r['air_yards_share']) < 1e-8:
                    r['team_air_yards'] = value
                    r['air_yards_verified'] = 1
                    r['_source'] = 'JJ Stats; air denominator reconstructed from consistent archived shares (internal check only)'
    if args.retain_zero_target_games:
        saved = {}
        for r in all_rows:
            if r['team_air_yards'] is not None:
                saved.setdefault((r['game_id'],r['team']), set()).add(r['team_air_yards'])
        available = dict(recovered)
        available.update({k:next(iter(v)) for k,v in saved.items() if len(v)==1})
        rows = [retain_zero_target(r, available.get((r['game_id'],r['team']))) for r in rows]
    accepted, rejected, reasons = [], [], Counter()
    for row in rows:
        converted, excluded = convert(row)
        if excluded:
            reasons.update(excluded)
            rejected.append({'game_id':row['game_id'], 'player':row['player'], 'reasons':excluded})
        else:
            accepted.append(converted)
    report = audit(accepted)
    summary = dict(source_sha256=hashlib.sha256(args.database.read_bytes()).hexdigest(),
                   air_denominator_recovery_enabled=args.recover_air_denominators, recovered_team_game_candidates=len(recovered), archived_wr_te_rows=len(rows), eligible_rows=len(accepted), excluded_rows=len(rejected),
                   exclusion_reasons=dict(reasons), eligible_by_week=dict(Counter(r['week'] for r in accepted)),
                   provisional_identity_rows=sum(r['player_id'].startswith('jj-local:') for r in accepted),
                   canonical_audit=report,
                   limitations=['Uploaded snapshot; freshness is recorded by its SHA256, not inferred from filename.',
                     'Exclusion reasons overlap. Excluded rows are not zero-filled.',
                     'Eligible sample is incomplete and unsuitable for training a calibrated score.',
                     'Database and derived player records stay local; public report contains counts only.'])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    if not report['passed']:
        print('FAIL: canonical audit; see report. No CSV exported.')
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED+['player','route_source_url'])
        writer.writeheader()
        writer.writerows(accepted)
    args.output.with_suffix('.excluded.json').write_text(json.dumps(rejected, indent=2), encoding='utf-8')
    print(f'PASS: {len(accepted)} eligible / {len(rows)} archived WR/TE rows')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
