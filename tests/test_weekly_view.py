import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_weekly_view import build_rows,render


class WeeklyViewTests(unittest.TestCase):
    models={'WR':{'weights':{'route_share':1.,'target_share':0.,'air_yard_share':0.}}}

    def row(self,week,routes,denominator):
        return dict(player='Test',team='ABC',position='WR',season=2026,week=week,
            routes=routes,team_route_opportunities=denominator,targets=1,team_targets=10,
            receiving_air_yards=-2,team_receiving_air_yards=100,fantasy_points_ppr=5)

    def test_three_week_share_is_ratio_of_sums(self):
        rows=build_rows(pd.DataFrame([self.row(1,10,10),self.row(2,0,40),self.row(3,10,50)]),self.models)
        week3=next(r for r in rows if r['week']==3)
        self.assertEqual(week3['rolling_score'],20)
        self.assertEqual(week3['rolling_games'],3)
        self.assertEqual(week3['ays'],-2)

    def test_gap_breaks_window_and_delta_without_zero_imputation(self):
        rows=build_rows(pd.DataFrame([self.row(1,10,10),self.row(3,10,50)]),self.models)
        week3=next(r for r in rows if r['week']==3)
        self.assertEqual(week3['rolling_games'],1)
        self.assertIsNone(week3['delta'])
        self.assertEqual(week3['rolling_signal'],'Janela incompleta')

    def test_payload_cannot_terminate_script(self):
        html=render([{'player':'</script><script>alert(1)</script>'}],{},'__PAYLOAD__')
        self.assertNotIn('</script>',html)
