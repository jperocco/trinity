import unittest
from scripts.import_jj import convert
from tests.test_data import game

class JJImportTests(unittest.TestCase):
    def row(self, **updates):
        r = game()
        r.update(routes_run=20, team_routes=40, team_air_yards=200,
                 route_is_estimate=0, route_source='PFF public', air_yards_verified=1,
                 player='Example', route_source_url='https://www.pff.com/example')
        r.update(updates)
        return r

    def test_real_counts_are_exported(self):
        row, reasons = convert(self.row())
        self.assertEqual(reasons, [])
        self.assertEqual(row['routes'], '20')
        self.assertEqual(row['team_route_opportunities'], '40')

    def test_estimate_not_substituted(self):
        row, reasons = convert(self.row(route_is_estimate=1))
        self.assertIsNone(row)
        self.assertIn('routes_not_confirmed_pff', reasons)

    def test_missing_data_not_zero_filled(self):
        row, reasons = convert(self.row(team_air_yards=None))
        self.assertIsNone(row)
        self.assertIn('missing_team_receiving_air_yards', reasons)

