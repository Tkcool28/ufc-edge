from decimal import Decimal
import unittest

from src.ufc_edge.data.parsing import (
    feet_inches_to_cm,
    inches_to_cm,
    landed_attempted,
    mmss_to_seconds,
    nonnegative_int,
    pounds,
    round_number,
    text_or_none,
)


class CanonicalParsingTests(unittest.TestCase):
    def test_null_text(self):
        for value in (None, "", " -- ", "N/A", "null"):
            self.assertIsNone(text_or_none(value))
        self.assertEqual(text_or_none("0"), "0")

    def test_nonnegative_int(self):
        self.assertEqual(nonnegative_int("0"), 0)
        self.assertEqual(nonnegative_int(" 12 "), 12)
        with self.assertRaises(ValueError):
            nonnegative_int("1.0")
        with self.assertRaises(ValueError):
            nonnegative_int("-1")

    def test_round_number_matches_greco_transport(self):
        self.assertEqual(round_number("Round 1"), 1)
        self.assertEqual(round_number("5"), 5)
        with self.assertRaises(ValueError):
            round_number("Round 0")
        with self.assertRaises(ValueError):
            round_number("R1")

    def test_mmss(self):
        self.assertEqual(mmss_to_seconds("3:38"), 218)
        self.assertEqual(mmss_to_seconds("0:00"), 0)
        with self.assertRaises(ValueError):
            mmss_to_seconds("3:60")
        with self.assertRaises(ValueError):
            mmss_to_seconds("218")

    def test_landed_attempted_matches_greco_transport(self):
        self.assertEqual(landed_attempted("3 of 5"), (3, 5))
        self.assertEqual(landed_attempted("0 of 0"), (0, 0))
        with self.assertRaises(ValueError):
            landed_attempted("6 of 5")
        with self.assertRaises(ValueError):
            landed_attempted("3/5")

    def test_inches_and_feet_inches(self):
        self.assertEqual(inches_to_cm('72"'), Decimal("182.88"))
        self.assertEqual(feet_inches_to_cm("5' 11\""), Decimal("180.34"))
        with self.assertRaises(ValueError):
            feet_inches_to_cm("5' 12\"")

    def test_pounds_does_not_silently_drop_zero(self):
        self.assertEqual(pounds("0.00"), Decimal("0.00"))
        self.assertIsNone(pounds("0.00", zero_is_missing=True))
        self.assertEqual(pounds("205 lbs"), Decimal("205"))
        with self.assertRaises(ValueError):
            pounds("-1")


if __name__ == "__main__":
    unittest.main()
