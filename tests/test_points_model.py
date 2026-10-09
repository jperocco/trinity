import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from train_points_model import fit,export,project


class PointsModelTests(unittest.TestCase):
    def test_export_preserves_fitted_predictions(self):
        data=pd.DataFrame({'targets_per_game':[1.,2.,4.,6.,9.], 'target_share':[.03,.07,.12,.2,.3], 'future_ppr':[2.,3.,6.,9.,15.]})
        features=['targets_per_game','target_share']
        fitted=fit(data,features);model=export(fitted,features,20)
        predicted=[project(row,model)[0] for row in data.to_dict('records')]
        np.testing.assert_allclose(predicted,np.maximum(0,fitted.predict(data[features])),atol=1e-10)

    def test_missing_input_never_becomes_zero(self):
        model={'features':['target_share'],'coefficients':{'target_share':10},'intercept':0,'score_anchor_ppr':20}
        with self.assertRaises(ValueError):project({},model)

    def test_score_has_fixed_anchor_and_bounds(self):
        model={'features':['target_share'],'coefficients':{'target_share':100},'intercept':0,'score_anchor_ppr':20}
        self.assertEqual(project({'target_share':.2},model),(20,9))
        self.assertGreater(project({'target_share':.3},model)[1],9)
        self.assertLess(project({'target_share':.3},model)[1],10)
