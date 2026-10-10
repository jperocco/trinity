import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from fit_original_trinity import matrix, predict


class OriginalTrinityFitTests(unittest.TestCase):
    def test_anchored_score_is_zero_and_monotonic(self):
        beta = np.array([0., 1., 1., 1.])
        points = predict(np.array([[0., 0., 0.], [.5, .5, .5], [1., 1., 1.]]), beta, True)
        self.assertEqual(points[0], 0.)
        self.assertTrue(np.all(np.diff(points) > 0))
        self.assertTrue(np.all(points < 10))

    def test_redzone_uses_games_and_missing_is_not_zero(self):
        row = dict(target_share=20., yprr=2., air_yard_share=25., redzone_targets=6., games=2)
        self.assertEqual(matrix([row], 'linear').tolist(), [[.5, .5, .5, 1.]])
        del row['redzone_targets']
        with self.assertRaises(KeyError): matrix([row], 'linear')
