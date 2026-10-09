"""Cross-check supplied annual FP exports against local nflverse REG player stats.

Identity resolution uses unique normalized exact name + position only; no fuzzy
matching and no overwrite of source data. Missing weekly rows are not games played.
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


def identity(name, position):
    name = unicodedata.normalize('NFKD', str(name))
    name = ''.join(c for c in name if not unicodedata.combining(c))
    # Preserve suffix letters to avoid conflating names of different players.
    return re.sub(r'[^a-z0-9]', '', name.casefold()) + '|' + position


def suffix_identity(name, position):
    name = re.sub(r'\s+(?:jr\.?|sr\.?|ii|iii|iv)$', '', str(name).strip(), flags=re.I)
    return identity(name, position)


def reconcile(fp_dir, nfl_dir, output):
    summary, crosswalk = {}, []
    for year in range(2021, 2026):
        fp = pd.read_csv(fp_dir / f'receiving_advanced_{year}.csv')
        nfl = pd.read_csv(nfl_dir / f'player_stats_{year}.csv', low_memory=False)
        nfl = nfl[(nfl.season_type == 'REG') & nfl.position.isin(['WR', 'TE'])].copy()
        nfl['identity'] = [identity(n, p) for n, p in zip(nfl.player_display_name, nfl.position)]
        ids = nfl.groupby('identity').player_id.agg(lambda x: sorted(set(x)))
        nfl['suffix_identity'] = [suffix_identity(n,p) for n,p in zip(nfl.player_display_name,nfl.position)]
        suffix_ids = nfl.groupby('suffix_identity').player_id.agg(lambda x: sorted(set(x)))
        fp['identity'] = [identity(n, p) for n, p in zip(fp.Name, fp.POS)]
        ambiguous = set(ids[ids.map(len) != 1].index)
        fp['player_id'] = fp.identity.map({k:v[0] for k,v in ids.items() if len(v) == 1})
        fp['match_method'] = np.where(fp.player_id.notna(), 'normalized_exact', 'unmatched')
        for index,row in fp[fp.player_id.isna()].iterrows():
            candidate = suffix_ids.get(suffix_identity(row.Name,row.POS), [])
            if len(candidate) == 1 and row.identity not in ambiguous:
                fp.loc[index,'player_id'] = candidate[0]
                fp.loc[index,'match_method'] = 'unique_suffix_variant'
        fp['duplicate'] = fp.duplicated('identity', keep=False)
        for _, row in fp.iterrows():
            crosswalk.append(dict(season=year, name=row.Name, position=row.POS,
                player_id=None if pd.isna(row.player_id) else row.player_id,
                status='ambiguous' if row.identity in ambiguous else 'unmatched' if pd.isna(row.player_id) else 'matched',
                match_method=row.match_method,
                duplicate_source_row=bool(row.duplicate)))
        totals = nfl.groupby('player_id').agg(nfl_stat_rows=('week', 'nunique'),
            nfl_fp=('fantasy_points_ppr', 'sum'), nfl_rec=('receptions','sum'),
            nfl_yards=('receiving_yards','sum'), nfl_td=('receiving_tds','sum'),
            nfl_targets=('targets','sum'), nfl_air=('receiving_air_yards','sum'))
        matched = fp[fp.player_id.notna() & ~fp.duplicate].merge(totals, on='player_id', validate='one_to_one')
        matched['fp_delta'] = matched.FP - matched.nfl_fp
        matched['ppg_rounding_delta'] = matched['FP/G'] - matched.FP / matched.G
        def count_equal(left, right, tolerance):
            return int((np.abs(left-right) <= tolerance).sum())
        summary[str(year)] = dict(source_rows=len(fp), identity_matched_rows=int(fp.player_id.notna().sum()),
            unmatched_names=fp.loc[fp.player_id.isna(), ['Name','POS']].to_dict('records'),
            ambiguous_keys=sorted(ambiguous & set(fp.identity)), duplicate_source_rows=int(fp.duplicate.sum()),
            comparison_rows=len(matched),
            match_methods=fp.match_method.value_counts().to_dict(),
            receiving_counts_exact=dict(receptions=count_equal(matched.REC,matched.nfl_rec,0),
                yards=count_equal(matched.YDS,matched.nfl_yards,0), touchdowns=count_equal(matched.TD,matched.nfl_td,0),
                targets=count_equal(matched.TGT,matched.nfl_targets,0), air_yards=count_equal(matched.AY,matched.nfl_air,0)),
            receiving_count_mismatches=matched.loc[(matched.REC!=matched.nfl_rec)|(matched.YDS!=matched.nfl_yards)|(matched.TD!=matched.nfl_td),
                ['Name','POS','G','REC','nfl_rec','YDS','nfl_yards','TD','nfl_td']].to_dict('records'),
            source_games_less_than_stat_rows_detail=matched.loc[matched.G<matched.nfl_stat_rows,
                ['Name','POS','G','nfl_stat_rows']].to_dict('records'),
            total_ppr_within_0051=count_equal(matched.FP,matched.nfl_fp,.051),
            median_absolute_total_ppr_delta=float(matched.fp_delta.abs().median()),
            max_absolute_total_ppr_delta=float(matched.fp_delta.abs().max()),
            source_games_equal_stat_rows=count_equal(matched.G,matched.nfl_stat_rows,0),
            source_games_greater_than_stat_rows=int((matched.G>matched.nfl_stat_rows).sum()),
            source_games_less_than_stat_rows=int((matched.G<matched.nfl_stat_rows).sum()),
            source_ppg_rounding_consistent=int((matched.ppg_rounding_delta.abs()<=.051).sum()),
            source_ppg_missing=int(matched['FP/G'].isna().sum()),
            largest_ppr_differences=matched.loc[matched.fp_delta.abs().nlargest(5).index,
                ['Name','POS','G','FP','nfl_fp','fp_delta','nfl_stat_rows']].to_dict('records'))
    output.mkdir(parents=True, exist_ok=True)
    report = dict(method='Unique normalized exact name+position; unique suffix-variant fallback; no fuzzy matches',
        caveats=['nflverse stat rows are not a complete games-played ledger.',
                 'Cross-provider match is not proof of provider route/share semantics.',
                 'Receiving count and fantasy scoring differences are recorded, not corrected.'], years=summary)
    (output/'ANNUAL_RECONCILIATION.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    (output/'FP_PLAYER_CROSSWALK.json').write_text(json.dumps(crosswalk,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fp-dir',type=Path,default=Path('data/history/fantasypoints'))
    p.add_argument('--nfl-dir',type=Path,default=Path('data/raw/nflverse'))
    p.add_argument('--output-dir',type=Path,default=Path('docs'))
    a=p.parse_args()
    reconcile(a.fp_dir,a.nfl_dir,a.output_dir)
