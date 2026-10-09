import unittest
from trinity import REQUIRED, audit, aggregate

def game(week=1, **changes):
    row = dict.fromkeys(REQUIRED, 'x')
    row.update(player_id='p1', game_id=f'g{week}', team='ARI', season='2026',
               week=str(week), position='TE', played='1', routes='20',
               team_route_opportunities='40', targets='5', team_targets='25',
               receiving_air_yards='40', team_receiving_air_yards='200', fantasy_points_ppr='0')
    row.update(changes)
    return row

class DataTests(unittest.TestCase):
    def test_weighted_shares_and_zero_production_game(self):
        rows = [game(), game(2, routes='10', team_route_opportunities='10', fantasy_points_ppr='20')]
        self.assertTrue(audit(rows)['passed'])
        result = aggregate(rows)[0]
        self.assertAlmostEqual(result['route_share'], .6)
        self.assertEqual(result['ppr_per_game'], 10)

    def test_duplicate(self):
        self.assertFalse(audit([game(), game()])['passed'])

    def test_team_denominator_conflict(self):
        self.assertFalse(audit([game(), game(player_id='p2', team_targets='30')])['passed'])

    def test_negative_air_yards_preserved(self):
        row = game(receiving_air_yards='-10')
        self.assertTrue(audit([row])['passed'])
        self.assertTrue(audit([row])['flags'])
        self.assertEqual(aggregate([row])[0]['air_yard_share'], -.05)

    def test_missing_routes_and_nonfinite_rejected(self):
        self.assertFalse(audit([game(routes='')])['passed'])
        self.assertFalse(audit([game(targets='nan')])['passed'])

    def test_zero_denominator(self):
        row = game(routes='0', team_route_opportunities='0')
        self.assertTrue(audit([row])['passed'])
        self.assertIsNone(aggregate([row])[0]['route_share'])

    def test_route_definition_change_rejected(self):
        with self.assertRaises(ValueError):
            aggregate([game(), game(2, routes_definition='different')])

if __name__ == '__main__':
    unittest.main()
