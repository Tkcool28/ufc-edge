from decimal import Decimal
import unittest

from ufc_edge.data.physical_profile_reconciliation import agreement_category, official_stats, selection, validate_official_inches


class PhysicalProfileReconciliationTests(unittest.TestCase):
    def test_official_populated_greco_null_selects_official(self):
        value, status, checked = selection(field="height", canonical_value="", official_raw="72", trusted_identity=True)
        self.assertTrue(checked.accepted)
        self.assertEqual(value, Decimal("182.88"))
        self.assertEqual(status, "official_null_fill")

    def test_official_null_greco_populated_retains_greco(self):
        value, status, checked = selection(field="reach_arm", canonical_value="190.5", official_raw=None, trusted_identity=True)
        self.assertEqual(value, Decimal("190.5"))
        self.assertEqual(status, "greco_retained_populated")
        self.assertEqual(checked.reason, "source_null")

    def test_both_null_stays_null_and_never_becomes_zero(self):
        value, status, _ = selection(field="height", canonical_value=None, official_raw=None, trusted_identity=True)
        self.assertIsNone(value)
        self.assertEqual(status, "canonical_null_official_rejected_source_null")

    def test_malformed_and_implausible_official_values_are_rejected(self):
        for raw, reason in (("x", "non_numeric"), ("Infinity", "non_finite"), ("155", "outside_plausible_inches_48_90")):
            checked = validate_official_inches("height", raw)
            self.assertFalse(checked.accepted)
            self.assertEqual(checked.reason, reason)

    def test_rejected_official_falls_back_to_greco(self):
        value, status, checked = selection(field="height", canonical_value="180.34", official_raw="155", trusted_identity=True)
        self.assertEqual(value, Decimal("180.34"))
        self.assertEqual(status, "greco_retained_populated")
        self.assertEqual(checked.reason, "outside_plausible_inches_48_90")

    def test_required_disagreement_categories_are_distinct(self):
        self.assertEqual(agreement_category("182.88", Decimal("182.88"))[1], "exact_agreement")
        self.assertEqual(agreement_category("182.88", Decimal("183.515"))[1], "small_rounding_difference")
        self.assertEqual(agreement_category("182.88", Decimal("184.15"))[1], "half_inch_difference")
        self.assertEqual(agreement_category("182.88", Decimal("185.42"))[1], "one_inch_or_less_difference")
        self.assertEqual(agreement_category("180", Decimal("187.62"))[1], "greater_than_one_inch_difference")

    def test_trusted_identity_is_required(self):
        value, status, checked = selection(field="reach_arm", canonical_value="", official_raw="76", trusted_identity=False)
        self.assertIsNone(value)
        self.assertEqual(status, "canonical_null_untrusted_official_identity")
        self.assertTrue(checked.accepted)

    def test_only_explicit_official_profile_shapes_are_accepted(self):
        self.assertEqual(official_stats({"stats_height": "72", "stats_reach_arm": "75"}), {"height": "72", "reach_arm": "75", "reach_leg": None})
        self.assertIsNone(official_stats({"other": {"height": "72"}}))


if __name__ == "__main__":
    unittest.main()
