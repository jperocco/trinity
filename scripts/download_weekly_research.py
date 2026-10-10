"""Fetch version-locked public research inputs without touching FP/JJ archives."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen


def fetch(year):
    path = Path(f'data/research/ffopportunity/ep_weekly_{year}.csv')
    url = f'https://github.com/ffverse/ffopportunity/releases/download/v1.0.0-data/ep_weekly_{year}.csv'
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        body = urlopen(url, timeout=60).read()
        if not body.startswith(b'season,'):
            raise ValueError(f'Unexpected CSV for {year}')
        temporary = path.with_suffix('.download')
        temporary.write_bytes(body)
        temporary.replace(path)
    return year, path.stat().st_size


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=5) as pool:
        for result in pool.map(fetch, range(2021, 2026)):
            print(result)
