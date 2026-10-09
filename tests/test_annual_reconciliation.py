import unittest

from scripts.reconcile_annual import identity, suffix_identity


class AnnualReconciliationTests(unittest.TestCase):
    def test_normalized_name_preserves_position_and_suffix(self):
        self.assertEqual(identity('A.J. Brown','WR'), identity('AJ Brown','WR'))
        self.assertNotEqual(identity('John Smith Jr.','WR'),identity('John Smith','WR'))
        self.assertNotEqual(identity('John Smith','WR'),identity('John Smith','TE'))

    def test_suffix_fallback_is_exact_not_fuzzy(self):
        self.assertEqual(suffix_identity('Marvin Harrison Jr.','WR'),identity('Marvin Harrison','WR'))
        self.assertNotEqual(suffix_identity('Gabriel Davis','WR'),identity('Gabe Davis','WR'))
