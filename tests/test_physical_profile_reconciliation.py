from decimal import Decimal
import unittest

from ufc_edge.data.physical_profile_reconciliation import agreement_category, official_stats, recovery_selection, selection, validate_official_inches, validate_recovery_measurement


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
        for raw, reason in (("x", "non_numeric"), ("Infinity", "non_finite"), ("0.00", "source_zero_missing"), ("155", "outside_plausible_inches_48_90")):
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
        self.assertEqual(official_stats({"id": "abc", "attributes": {"stats_height": "72", "stats_reach_arm": "75", "stats_reach_leg": "40"}}), {"height": "72", "reach_arm": "75", "reach_leg": "40"})

    def test_unverified_mapping_cannot_emit_official_value(self):
        value, status, checked = selection(field="height", canonical_value="", official_raw="72", trusted_identity=True, mapping_verified=False)
        self.assertIsNone(value)
        self.assertEqual(status, "canonical_null_unverified_official_mapping")
        self.assertTrue(checked.accepted)

    def test_leg_reach_validates_but_canonical_enrichment_stays_disabled(self):
        value, status, checked = selection(field="reach_leg", canonical_value="", official_raw="41", trusted_identity=True, allow_fill=False)
        self.assertTrue(checked.accepted)
        self.assertIsNone(value)
        self.assertEqual(status, "official_validated_enrichment_disabled")

    def test_governed_supplemental_recovery_fills_null(self):
        value, status, checked = recovery_selection(
            field_name="reach_cm", canonical_value="", raw_value="75", raw_unit="in",
            review_status="accepted", resolution_status="RESOLVED_TRUSTED_MEASUREMENT",
        )
        self.assertTrue(checked.accepted)
        self.assertEqual(value, Decimal("190.50"))
        self.assertEqual(status, "supplemental_null_fill")

    def test_supplemental_cannot_overwrite_populated_prior_canonical(self):
        value, status, _ = recovery_selection(
            field_name="height_cm", canonical_value="182.88", raw_value="70", raw_unit="in",
            review_status="accepted", resolution_status="RESOLVED_TRUSTED_MEASUREMENT",
        )
        self.assertEqual(value, Decimal("182.88"))
        self.assertEqual(status, "prior_canonical_retained")

    def test_supplemental_cannot_overwrite_validated_official_fill(self):
        official, _, _ = selection(field="height", canonical_value="", official_raw="72", trusted_identity=True)
        value, status, _ = recovery_selection(
            field_name="height_cm", canonical_value=official, raw_value="70", raw_unit="in",
            review_status="accepted", resolution_status="RESOLVED_TRUSTED_MEASUREMENT",
        )
        self.assertEqual(value, Decimal("182.88"))
        self.assertEqual(status, "prior_canonical_retained")

    def test_conflicting_or_rejected_recovery_does_not_emit(self):
        value, status, _ = recovery_selection(
            field_name="reach_cm", canonical_value="", raw_value="", raw_unit="",
            review_status="quarantined", resolution_status="RESOLVED_CONFLICT_QUARANTINED",
        )
        self.assertIsNone(value)
        self.assertEqual(status, "supplemental_conflict_quarantined")

    def test_exhausted_recovery_remains_null(self):
        value, status, _ = recovery_selection(
            field_name="reach_cm", canonical_value="", raw_value="", raw_unit="",
            review_status="exhausted", resolution_status="EXHAUSTED_TRUSTED_SOURCES_NO_MEASUREMENT",
        )
        self.assertIsNone(value)
        self.assertEqual(status, "supplemental_exhausted_no_measurement")

    def test_recovery_malformed_and_implausible_values_rejected(self):
        for raw, unit in (("x", "in"), ("Infinity", "cm"), ("0", "in"), ("20", "in"), ("500", "cm")):
            self.assertFalse(validate_recovery_measurement("height_cm", raw, unit).accepted)

    def test_recovery_unit_conversion_is_deterministic(self):
        self.assertEqual(validate_recovery_measurement("reach_cm", "75", "in").value_cm, Decimal("190.50"))
        self.assertEqual(validate_recovery_measurement("reach_cm", "190.5", "cm").value_cm, Decimal("190.5"))

    def test_recovery_requires_explicit_units(self):
        checked = validate_recovery_measurement("reach_cm", "75", "")
        self.assertFalse(checked.accepted)
        self.assertEqual(checked.reason, "unsupported_or_missing_unit")

    def test_nonaccepted_resolution_cannot_emit_even_with_numeric_value(self):
        value, status, checked = recovery_selection(
            field_name="reach_cm", canonical_value="", raw_value="75", raw_unit="in",
            review_status="quarantined", resolution_status="RESOLVED_CONFLICT_QUARANTINED",
        )
        self.assertTrue(checked.accepted)
        self.assertIsNone(value)
        self.assertEqual(status, "supplemental_conflict_quarantined")


if __name__ == "__main__":
    unittest.main()
