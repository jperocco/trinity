import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from research_weekly_architecture import build_samples, OPPORTUNITY


class WeeklyArchitectureResearchTests(unittest.TestCase):
    def source(self):
        return pd.DataFrame([dict(player_id='a', season=2021, posteam='A', position='WR', week=w,
            rec_attempt=5., rec_attempt_team=30., rec_air_yards=50., rec_air_yards_team=300., ppr=10., xfp=9.) for w in [1, 2, 3, 4]])

    def test_future_outcome_cannot_change_features(self):
        source = self.source()
        before = build_samples(source)
        source.loc[source.week == 4, ['rec_attempt', 'ppr', 'xfp']] = [100., 200., 300.]
        after = build_samples(source)
        self.assertEqual(before[OPPORTUNITY+['cum_ppr', 'cum_xfp']].to_dict('records'), after[OPPORTUNITY+['cum_ppr', 'cum_xfp']].to_dict('records'))
        self.assertEqual(after.future_targets.tolist(), [100.])

    def test_gap_does_not_become_adjacent_week(self):
        source = self.source()
        source.loc[source.week == 4, 'week'] = 5
        self.assertTrue(build_samples(source).empty)
