import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from calibrate_trinity import fit_weights,score


class TrinityCalibrationTests(unittest.TestCase):
    def test_known_positive_weights_recovered(self):
        rng=np.random.default_rng(42)
        x=rng.uniform(0,100,(200,3))
        frame=pd.DataFrame(x,columns=['RTE %','TGT %','AY Share'])
        frame['FP/G']=2+x@np.array([.03,.06,.01])
        model=fit_weights(frame)
        np.testing.assert_allclose(list(model['weights'].values()),[.3,.6,.1],atol=1e-10)
        self.assertAlmostEqual(model['intercept'],2)

    def test_unhelpful_negative_effect_gets_no_forced_weight(self):
        rng=np.random.default_rng(6)
        x=rng.uniform(0,100,(400,3))
        frame=pd.DataFrame(x,columns=['RTE %','TGT %','AY Share'])
        frame['FP/G']=x[:,1]-.5*x[:,0]
        weights=fit_weights(frame)['weights']
        self.assertEqual(weights['route_share'],0)
        self.assertAlmostEqual(sum(weights.values()),1)
        self.assertTrue(all(w>=0 for w in weights.values()))

    def test_score_ratio_units_and_negative_air_preserved(self):
        model={'weights':{'route_share':.2,'target_share':.6,'air_yard_share':.2}}
        self.assertAlmostEqual(float(score([.8,.2,-.1],model)),26)
