"""Plan or run documented PFF receiving exports. Requires authenticated Restish."""
import argparse
import shutil
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--seasons', nargs='+', type=int, default=list(range(2021, 2026)))
parser.add_argument('--weeks', nargs='+', type=int, default=list(range(1, 19)))
parser.add_argument('--output', type=Path, default=Path('data/raw/pff'))
parser.add_argument('--execute', action='store_true')
args = parser.parse_args()
if any(s < 2021 for s in args.seasons) or any(w < 1 or w > 18 for w in args.weeks):
    parser.error('regular-season years >=2021 and weeks 1–18 only')
if args.execute and not shutil.which('restish'):
    parser.error('Restish is not installed; see docs/ACQUISITION.md')
for season in sorted(set(args.seasons)):
    for week in sorted(set(args.weeks)):
        target = args.output / f'receiving-{season}-week-{week}.csv'
        if target.exists():
            print(f'SKIP existing: {target}')
            continue
        command = ['restish', 'pff', 'receiving', '--league', 'nfl', '--season', str(season), '--week', str(week), '--export', 'true', '--rsh-print', 'b']
        if not args.execute:
            print(' '.join(command) + f' > {target}')
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.csv.part')
        try:
            with temporary.open('wb') as stream:
                subprocess.run(command, stdout=stream, check=True)
            header = temporary.read_text(encoding='utf-8-sig').splitlines()[0]
            if ',' not in header or header.startswith(('{', '<')):
                raise ValueError('response is not a CSV report')
            temporary.rename(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        print(f'SAVED: {target}')
