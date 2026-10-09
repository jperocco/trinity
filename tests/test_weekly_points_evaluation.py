import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from evaluate_weekly_points import forward_pairs


class WeeklyPointsEvaluationTests(unittest.TestCase):
    def test_missing_week_is_not_zero_or_next_available_game(self):
        rows = pd.DataFrame({'identity': ['a', 'a', 'a', 'b', 'b'], 'week': [1, 2, 3, 1, 3],
            'has_observation': [True, False, True, True, True], 'ppr': [5., None, 9., 4., 8.]})
        self.assertTrue(forward_pairs(rows).empty)

    def test_future_points_attach_only_to_previous_calendar_week(self):
        rows = pd.DataFrame({'identity': ['a', 'a', 'a'], 'week': [1, 2, 3],
            'has_observation': [True, True, True], 'ppr': [5., 8., 12.], 'cumulative_ppr': [5., 6.5, 25./3]})
        pairs = forward_pairs(rows)
        self.assertEqual(pairs.week.tolist(), [1, 2])
        self.assertEqual(pairs.future_ppr.tolist(), [8., 12.])
        self.assertEqual(pairs.cumulative_ppr.tolist(), [5., 6.5])
