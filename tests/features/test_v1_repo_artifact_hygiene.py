import unittest

from tools.features.check_repo_artifact_hygiene import find_violations, violation


class RepoArtifactHygieneTests(unittest.TestCase):
    def test_permanent_validation_artifact_namespace_is_allowed(self):
        allowed = [
            "governance/model_validation_bucket_v1/calibration/M1_CALIBRATION_DIAGNOSTIC_V1.csv",
            "governance/model_validation_bucket_v1/calibration/example.parquet",
            "governance/model_validation_bucket_v1/example.feather",
        ]
        self.assertEqual(find_violations(allowed), [])

    def test_matrix_like_files_elsewhere_remain_rejected(self):
        rejected = [
            "reports/example.csv",
            "models/m1/example.parquet",
            "governance/other_namespace/example.feather",
        ]
        self.assertEqual(
            [reason for _, reason in find_violations(rejected)],
            ["matrix-like file outside governed namespace"] * 3,
        )

    def test_generated_directories_are_rejected_everywhere(self):
        rejected = [
            "run/a.csv",
            "foo/runs/a.json",
            "governance/model_validation_bucket_v1/output/a.csv",
            "data/raw/generated/a.csv",
            "feature_store/a.parquet",
        ]
        self.assertEqual(
            [reason for _, reason in find_violations(rejected)],
            ["generated/run/output directory"] * len(rejected),
        )

    def test_existing_governed_data_rules_are_unchanged(self):
        self.assertIsNone(violation("data/raw/source.csv"))
        self.assertIsNone(violation("data/supplemental/evidence.parquet"))
        self.assertEqual(
            violation("data/canonical/v0/new_matrix.csv"),
            "matrix-like file outside governed namespace",
        )


if __name__ == "__main__":
    unittest.main()
