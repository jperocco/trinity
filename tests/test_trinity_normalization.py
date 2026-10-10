import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from research_trinity_normalization import dominance_conflicts, project


class TrinityNormalizationTests(unittest.TestCase):
    def test_zero_anchor_monotonic_and_bounded(self):
        parameters=np.zeros(12)
        y=project(np.array([[0.,0.,0.,0.],[1.,1.,1.,1.],[2.,2.,2.,2.]]),parameters)
        self.assertEqual(y[0],0.)
        self.assertTrue(np.all(np.diff(y)>0))
        self.assertTrue(np.all(y<10.))

    def test_dominance_requires_all_metrics_and_uses_rz_per_game(self):
        a=dict(player='a',score=6.,target_share=30.,yprr=3.,air_yard_share=40.,redzone_targets=4.,games=4)
        b=dict(player='b',score=7.,target_share=20.,yprr=2.,air_yard_share=30.,redzone_targets=2.,games=2)
        self.assertEqual(len(dominance_conflicts([a,b])),1)
        b['yprr']=4.
        self.assertEqual(dominance_conflicts([a,b]),[])
