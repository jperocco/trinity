import unittest

import numpy as np
import pandas as pd

from scripts.backtest_annual import evaluate, bootstrap_delta, transitions


class AnnualBacktestTests(unittest.TestCase):
    def test_holdout_outcomes_do_not_change_fit_or_alpha(self):
        rng = np.random.default_rng(5)
        rows = []
        for year in range(2022, 2026):
            for pos in ['WR', 'TE']:
                for i in range(12):
                    x = rng.uniform(1, 30)
                    rows.append(dict(POS=pos, outcome_year=year, outcome=x/2,
                                     **{'RTE %': x*3, 'TGT %': x, 'AY Share': x*1.2, 'FP/G': x/2}))
        data = pd.DataFrame(rows)
        first = evaluate(data)
        data.loc[data.outcome_year == 2025, 'outcome'] += 50
        second = evaluate(data)
        for pos in first:
            for name, model in first[pos]['models'].items():
                other = second[pos]['models'][name]
                self.assertEqual(model['alpha'], other['alpha'])
                self.assertEqual(model['coefficients_per_source_unit'], other['coefficients_per_source_unit'])

    def test_paired_delta_sign(self):
        result = bootstrap_delta(np.array([1., 2.]), np.array([1., 2.]), np.array([2., 3.]))
        self.assertEqual(result['delta_mae'], -1.)
        self.assertEqual(result['ci95'], [-1., -1.])

    def test_identity_merge_never_crosses_position(self):
        frames = {y:pd.DataFrame({'identity':['Same|WR','Same|TE'], 'FP/G':[1., 9.]}) for y in range(2021,2026)}
        pairs = transitions(frames)
        self.assertTrue((pairs['FP/G'] == pairs.outcome).all())
        self.assertEqual(len(pairs), 8)
