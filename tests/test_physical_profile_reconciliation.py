from decimal import Decimal
import csv
from pathlib import Path
import unittest

from ufc_edge.data.physical_profile_reconciliation import agreement_category, live_ufcstats_requirement, live_ufcstats_selection, official_stats, recovery_selection, selection, validate_official_inches, validate_recovery_measurement


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


    def test_local_snapshot_null_marks_live_check_required(self):
        self.assertEqual(live_ufcstats_requirement("", pinned_live_checked=False), "LIVE_UFCSTATS_CHECK_REQUIRED")
        self.assertEqual(live_ufcstats_requirement("180.34", pinned_live_checked=False), "LOCAL_SOURCE_POPULATED")

    def test_pinned_live_ufcstats_populated_fills_null(self):
        value, status, checked = live_ufcstats_selection(field_name="reach_cm", canonical_value="", raw_value_inches="73", identity_verified=True, live_state="POPULATED")
        self.assertTrue(checked.accepted)
        self.assertEqual(value, Decimal("185.42"))
        self.assertEqual(status, "live_ufcstats_null_fill")

    def test_live_ufcstats_cannot_overwrite_existing_canonical(self):
        value, status, _ = live_ufcstats_selection(field_name="reach_cm", canonical_value="190.5", raw_value_inches="73", identity_verified=True, live_state="POPULATED")
        self.assertEqual(value, Decimal("190.5"))
        self.assertEqual(status, "prior_canonical_retained")

    def test_live_ufcstats_outranks_supplemental_for_null_field(self):
        live, status, _ = live_ufcstats_selection(field_name="reach_cm", canonical_value="", raw_value_inches="71", identity_verified=True, live_state="POPULATED")
        later, later_status, _ = recovery_selection(field_name="reach_cm", canonical_value=live, raw_value="73.6", raw_unit="in", review_status="quarantined", resolution_status="RESOLVED_CONFLICT_QUARANTINED")
        self.assertEqual(status, "live_ufcstats_null_fill")
        self.assertEqual(later, Decimal("180.34"))
        self.assertEqual(later_status, "prior_canonical_retained")

    def test_live_ufcstats_resolves_lower_tier_conflict(self):
        value, status, _ = live_ufcstats_selection(field_name="reach_cm", canonical_value="", raw_value_inches="72", identity_verified=True, live_state="POPULATED")
        self.assertEqual(value, Decimal("182.88"))
        self.assertEqual(status, "live_ufcstats_null_fill")

    def test_live_checked_null_remains_null_with_explicit_status(self):
        value, status, checked = live_ufcstats_selection(field_name="height_cm", canonical_value="", raw_value_inches="", identity_verified=True, live_state="CHECKED_STILL_NULL")
        self.assertIsNone(value)
        self.assertEqual(status, "live_ufcstats_checked_still_null")
        self.assertEqual(checked.reason, "source_null")

    def test_pinned_live_provenance_has_url_and_retrieval_timestamp(self):
        rows = list(csv.DictReader(Path("data/raw/ufcstats_live_recovery/35053621411/observations.csv").open(encoding="utf-8")))
        self.assertEqual(len(rows), 11)
        self.assertTrue(all(r["ufcstats_url"].startswith("http://ufcstats.com/fighter-details/") for r in rows))
        self.assertTrue(all(r["retrieved_at"].endswith("Z") for r in rows))
        self.assertTrue(all(r["identity_verified"] == "true" for r in rows))

    def test_live_malformed_value_is_rejected(self):
        value, status, checked = live_ufcstats_selection(field_name="reach_cm", canonical_value="", raw_value_inches="x", identity_verified=True, live_state="POPULATED")
        self.assertIsNone(value)
        self.assertEqual(status, "live_ufcstats_rejected_non_numeric")
        self.assertFalse(checked.accepted)

    def test_live_implausible_value_is_rejected(self):
        value, status, checked = live_ufcstats_selection(field_name="height_cm", canonical_value="", raw_value_inches="155", identity_verified=True, live_state="POPULATED")
        self.assertIsNone(value)
        self.assertTrue(status.startswith("live_ufcstats_rejected_outside_plausible"))
        self.assertFalse(checked.accepted)

    def test_canonical_builder_consumes_pinned_recovery_without_network(self):
        source = Path("pipelines/build_physical_profile_canonical_reconciliation_v1.py").read_text(encoding="utf-8")
        self.assertIn('data/raw/ufcstats_live_recovery/35053621411', source)
        self.assertNotIn("urlopen(", source)
        self.assertNotIn("requests.", source)

    def test_ordinary_canonical_build_is_offline_by_contract(self):
        fetch_source = Path("pipelines/fetch_ufcstats_live_physical_recovery_v1.py").read_text(encoding="utf-8")
        build_source = Path("pipelines/build_physical_profile_canonical_reconciliation_v1.py").read_text(encoding="utf-8")
        self.assertIn("build_opener", fetch_source)
        self.assertNotIn("build_opener", build_source)
        self.assertNotIn("urllib", build_source)

    def test_live_target_scope_is_bounded_and_unique(self):
        rows = list(csv.DictReader(Path("data/supplemental/ufcstats_live_recovery_targets_v1.csv").open(encoding="utf-8")))
        keys = {(r["fighter_id"], r["field_name"]) for r in rows}
        self.assertEqual(len(rows), 11)
        self.assertEqual(len(keys), 11)
        self.assertTrue(all(r["field_name"] in {"height_cm", "reach_cm"} for r in rows))


if __name__ == "__main__":
    unittest.main()
