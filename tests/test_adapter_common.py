from __future__ import annotations

import unittest
from datetime import date

from pipelines.adapters.common import (
    normalize_text,
    parse_height_cm,
    parse_integral_count,
    parse_landed_attempted,
    parse_mmss,
    parse_percent_qa,
    parse_reach_cm,
    parse_round_number,
    parse_ufcstats_date,
    parse_weight_lbs,
)


class AdapterCommonTests(unittest.TestCase):
    def test_missing_markers(self) -> None:
        self.assertIsNone(normalize_text(None))
        self.assertIsNone(normalize_text(""))
        self.assertIsNone(normalize_text(" -- "))
        self.assertIsNone(normalize_text("---"))
        self.assertEqual(normalize_text("  Orthodox "), "Orthodox")

    def test_integral_count_observed_forms(self) -> None:
        self.assertEqual(parse_integral_count("0"), 0)
        self.assertEqual(parse_integral_count("5"), 5)
        self.assertEqual(parse_integral_count("0.0"), 0)
        self.assertEqual(parse_integral_count("4.0"), 4)
        self.assertIsNone(parse_integral_count(""))
        with self.assertRaises(ValueError):
            parse_integral_count("1.5")
        with self.assertRaises(ValueError):
            parse_integral_count(-1)

    def test_landed_attempted_observed_forms(self) -> None:
        self.assertEqual(parse_landed_attempted("3 of 5"), (3, 5))
        self.assertEqual(parse_landed_attempted("0 of 0"), (0, 0))
        self.assertEqual(parse_landed_attempted(" 11 of 20 "), (11, 20))
        self.assertIsNone(parse_landed_attempted("--"))
        with self.assertRaises(ValueError):
            parse_landed_attempted("8 of 7")
        with self.assertRaises(ValueError):
            parse_landed_attempted("3/5")

    def test_control_time(self) -> None:
        self.assertEqual(parse_mmss("3:38"), 218)
        self.assertEqual(parse_mmss("0:00"), 0)
        self.assertEqual(parse_mmss("0:17"), 17)
        with self.assertRaises(ValueError):
            parse_mmss("1:60")
        with self.assertRaises(ValueError):
            parse_mmss("3.38")

    def test_percent_is_qa_only_parser(self) -> None:
        self.assertEqual(parse_percent_qa("60%"), 60)
        self.assertEqual(parse_percent_qa("0%"), 0)
        self.assertEqual(parse_percent_qa("100%"), 100)
        self.assertIsNone(parse_percent_qa("---"))
        with self.assertRaises(ValueError):
            parse_percent_qa("101%")

    def test_round_label(self) -> None:
        self.assertEqual(parse_round_number("Round 1"), 1)
        self.assertEqual(parse_round_number("round 5"), 5)
        self.assertEqual(parse_round_number("3"), 3)
        with self.assertRaises(ValueError):
            parse_round_number("Round 0")

    def test_tott_height_reach_weight_date(self) -> None:
        self.assertAlmostEqual(parse_height_cm("5' 11\""), 180.34)
        self.assertAlmostEqual(parse_height_cm("6' 2\""), 187.96)
        self.assertIsNone(parse_height_cm("--"))
        with self.assertRaises(ValueError):
            parse_height_cm("5' 12\"")

        self.assertAlmostEqual(parse_reach_cm('66"'), 167.64)
        self.assertAlmostEqual(parse_reach_cm('80"'), 203.20)
        self.assertIsNone(parse_reach_cm("--"))

        self.assertEqual(parse_weight_lbs("155 lbs."), 155.0)
        self.assertEqual(parse_weight_lbs("265 lbs."), 265.0)
        self.assertIsNone(parse_weight_lbs("--"))

        self.assertEqual(parse_ufcstats_date("Jul 03, 1983"), date(1983, 7, 3))
        self.assertEqual(parse_ufcstats_date("Feb 01, 1994"), date(1994, 2, 1))
        self.assertIsNone(parse_ufcstats_date("--"))


if __name__ == "__main__":
    unittest.main()
