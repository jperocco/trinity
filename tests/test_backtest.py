import unittest
from scripts.prepare_backtest import samples
from tests.test_data import game

class ForwardTests(unittest.TestCase):
    def test_future_not_in_features(self):
        rows=[game(1,fantasy_points_ppr='2'),game(2,fantasy_points_ppr='100',targets='20')]
        result=samples(rows,1,1)[0]
        self.assertEqual(result['ppr_per_game'],2)
        self.assertEqual(result['target_share'],.2)
        self.assertEqual(result['future_ppr_per_game'],100)

    def test_missing_week_not_zero_filled(self):
        self.assertEqual(samples([game(1),game(3)],1,1),[])

    def test_trade_not_joined_across_teams(self):
        self.assertEqual(samples([game(1),game(2,team='NYJ')],1,1),[])

    def test_provisional_ids_not_training_samples(self):
        self.assertEqual(samples([game(1,player_id='jj-local:x'),game(2,player_id='jj-local:x')],1,1),[])
