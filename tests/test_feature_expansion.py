import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from evaluate_feature_expansion import chronological_split, clustered_delta


class FeatureExpansionTests(unittest.TestCase):
    def test_temporal_split_excludes_current_and_future_outcomes(self):
        pairs = pd.DataFrame({'outcome_year': [2022, 2023, 2024, 2025]})
        train, test = chronological_split(pairs, 2024)
        self.assertEqual(train.outcome_year.tolist(), [2022, 2023])
        self.assertEqual(test.outcome_year.tolist(), [2024])

    def test_bootstrap_keeps_repeated_players_as_clusters(self):
        rows = pd.DataFrame({'identity': ['a', 'a', 'b'], 'future_ppr': [1., 1., 1.], 'candidate': [1., 1., 1.], 'baseline': [2., 2., 2.]})
        result = clustered_delta(rows, 'candidate', 'baseline')
        self.assertEqual(result['player_clusters'], 2)
        self.assertEqual(result['delta_mae'], -1.)
        self.assertEqual(result['ci95'], [-1., -1.])
