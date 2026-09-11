"""Public F01 contract-driven V1 materializer API and deterministic manifests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from .contract import (
    load_feature_catalog,
    materialized_feature_names,
    validate_repository_contract,
)
from .history import CanonicalStore, parse_cutoff
from .state import (
    FighterState,
    MatchupState,
    StateBuilder,
    active_v1_features,
    selected_v1_names,
)


class MaterializerError(ValueError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def deterministic_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProvenanceManifest:
    deterministic: dict[str, Any]
    deterministic_payload_sha256: str
    generated_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class V1Materializer:
    """Contract-driven reference materializer for the current V1 surface."""

    def __init__(self, root: Path | None = None):
        self.root = (root or Path(__file__).resolve().parents[3]).resolve()
        summary = validate_repository_contract(self.root)
        if summary["feature_contract_version"] != "0.1.2-draft":
            raise MaterializerError("F01 requires feature contract 0.1.2-draft")
        self.catalog = load_feature_catalog(self.root)
        if self.catalog["elapsed_exposure_policy"]["allowed_sources"] != ["ruleset_registry_v1"]:
            raise MaterializerError("F01 requires elapsed_exposure_policy.allowed_sources=[ruleset_registry_v1]")
        self.store = CanonicalStore(self.root)
        self.builder = StateBuilder(self.store, self.catalog)

        contract_names = set(materialized_feature_names(self.catalog))
        v1_names = set(selected_v1_names(self.catalog))
        if not v1_names <= contract_names:
            raise MaterializerError(f"V1 naming escaped F00 contract: {sorted(v1_names-contract_names)}")
        self.all_v1_names = tuple(sorted(v1_names))

    def concepts(self, consumer: str | None = None) -> list[str]:
        return [feature["feature_name"] for feature in active_v1_features(self.catalog, consumer)]

    def names(self, consumer: str | None = None) -> list[str]:
        return selected_v1_names(self.catalog, consumer)

    def _validate_target_request(
        self,
        requested_fighter_ids: tuple[str, ...],
        prediction_as_of: str,
        target_fight_id: str | None,
    ) -> None:
        """Fail closed before state construction when target identity/cutoff conflict.

        Canonical v0 only proves event-date chronology. If a supplied target's
        event date is strictly before the cutoff date, that fight is historical
        under the same rule used by ``prior_fights`` and therefore cannot also
        be treated as the prediction target.
        """
        if target_fight_id is None:
            return
        target = self.store.require_fight(target_fight_id)
        target_fighters = {target.fighter_a_id, target.fighter_b_id}
        missing = [fighter_id for fighter_id in requested_fighter_ids if fighter_id not in target_fighters]
        if missing:
            raise MaterializerError(
                f"target fight {target_fight_id} does not include requested fighter(s): {sorted(missing)}"
            )
        cutoff_date = parse_cutoff(prediction_as_of).date()
        if target.event_date < cutoff_date:
            raise MaterializerError(
                f"target fight {target_fight_id} on {target.event_date.isoformat()} is historical "
                f"at prediction cutoff date {cutoff_date.isoformat()}"
            )

    def materialize_fighter(
        self,
        fighter_id: str,
        prediction_as_of: str,
        *,
        target_fight_id: str | None = None,
        consumer: str | None = None,
    ) -> FighterState:
        self._validate_target_request((fighter_id,), prediction_as_of, target_fight_id)
        return self.builder.materialize_fighter(
            fighter_id,
            prediction_as_of,
            target_fight_id=target_fight_id,
            consumer=consumer,
        )

    def materialize_matchup(
        self,
        fighter_a_id: str,
        fighter_b_id: str,
        prediction_as_of: str,
        *,
        target_fight_id: str | None = None,
        consumer: str | None = None,
    ) -> MatchupState:
        self._validate_target_request(
            (fighter_a_id, fighter_b_id), prediction_as_of, target_fight_id
        )
        return self.builder.materialize_matchup(
            fighter_a_id,
            fighter_b_id,
            prediction_as_of,
            target_fight_id=target_fight_id,
            consumer=consumer,
        )

    def manifest(
        self,
        *,
        prediction_cutoff: str,
        row_count: int,
        consumer: str | None,
        materialized_names: list[str],
        code_commit: str | None = None,
        generated_at_utc: str | None = None,
    ) -> ProvenanceManifest:
        manifest_path = self.root / "data/canonical/v0/manifest.json"
        freeze_path = self.root / "provenance/data_phase_freeze_v0.json"
        canonical_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        selected_statuses = sorted({
            feature["status"] for feature in active_v1_features(self.catalog, consumer)
        })
        deterministic = {
            "feature_contract_version": self.catalog["feature_contract_version"],
            "feature_catalog_sha256": _sha256(self.root / "features/feature_catalog.yaml"),
            "feature_schema_sha256": _sha256(self.root / "features/feature_schema.json"),
            "leakage_registry_sha256": _sha256(self.root / "features/leakage_registry.yaml"),
            "data_contract_version": self.catalog["data_contract_version"],
            "data_freeze_sha256": _sha256(freeze_path),
            "data_freeze_status": freeze.get("status"),
            "canonical_manifest_sha256": _sha256(manifest_path),
            "canonical_manifest_build": canonical_manifest.get("build"),
            "materializer_code_commit": code_commit or _git_head(self.root),
            "prediction_cutoff": prediction_cutoff,
            "selected_consumer": consumer,
            "selected_statuses": selected_statuses,
            "fighter_orientation_policy": self.catalog["orientation_policy"],
            "window_policy": self.catalog["windows"],
            "shrinkage_policy": self.catalog["shrinkage_policies"],
            "elapsed_exposure_policy": self.catalog["elapsed_exposure_policy"],
            "materialized_feature_names": sorted(materialized_names),
            "row_count": int(row_count),
        }
        return ProvenanceManifest(
            deterministic=deterministic,
            deterministic_payload_sha256=deterministic_hash(deterministic),
            generated_at_utc=generated_at_utc or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )

    def bounded_real_validation(self) -> dict[str, Any]:
        """Exercise real canonical rows without writing a historical matrix."""
        fights = sorted(self.store.fights.values(), key=lambda f: (f.event_date, f.fight_id), reverse=True)
        cases: dict[str, tuple[str, str]] = {}
        for fight in fights:
            cutoff = f"{fight.event_date.isoformat()}T12:00:00Z"
            for fighter_id in (fight.fighter_a_id, fight.fighter_b_id):
                count = len(self.store.prior_fights(fighter_id, cutoff))
                if count >= 10 and "long_history" not in cases:
                    cases["long_history"] = (fighter_id, fight.fight_id)
                if 1 <= count <= 2 and "sparse_history" not in cases:
                    cases["sparse_history"] = (fighter_id, fight.fight_id)
                if count == 0 and "zero_prior_canonical_history" not in cases:
                    cases["zero_prior_canonical_history"] = (fighter_id, fight.fight_id)
            if len(cases) == 3:
                break
        if "long_history" not in cases or "sparse_history" not in cases:
            raise MaterializerError(f"bounded canonical validation could not find required history cases: {sorted(cases)}")

        validations: dict[str, Any] = {}
        for label, (fighter_id, fight_id) in sorted(cases.items()):
            fight = self.store.require_fight(fight_id)
            cutoff = f"{fight.event_date.isoformat()}T12:00:00Z"
            first = self.materialize_fighter(fighter_id, cutoff, target_fight_id=fight_id)
            second = self.materialize_fighter(fighter_id, cutoff, target_fight_id=fight_id)
            first_payload = first.audit_projection()
            second_payload = second.audit_projection()
            if first_payload != second_payload:
                raise MaterializerError(f"nondeterministic bounded materialization for {label}")
            validations[label] = {
                "fighter_id": fighter_id,
                "target_fight_id": fight_id,
                "prediction_as_of": cutoff,
                "prior_fight_count": len(self.store.prior_fights(fighter_id, cutoff)),
                "state_column_count": len(first.values),
                "state_sha256": deterministic_hash(first_payload),
            }

        # Real matchup orientation / interaction validation.
        long_fighter, long_fight_id = cases["long_history"]
        target = self.store.require_fight(long_fight_id)
        matchup = self.materialize_matchup(
            target.fighter_a_id,
            target.fighter_b_id,
            f"{target.event_date.isoformat()}T12:00:00Z",
            target_fight_id=target.fight_id,
        )
        reverse = self.materialize_matchup(
            target.fighter_b_id,
            target.fighter_a_id,
            f"{target.event_date.isoformat()}T12:00:00Z",
            target_fight_id=target.fight_id,
        )
        if matchup.projection() != reverse.projection():
            raise MaterializerError("matchup projection changed when provider/input fighter order was reversed")

        external_prior_count = 0
        for fighter_id, fight_id in cases.values():
            target = self.store.require_fight(fight_id)
            cutoff = f"{target.event_date.isoformat()}T12:00:00Z"
            external_prior_count += sum(
                1 for prior in self.store.prior_fights(fighter_id, cutoff)
                if (prior.promotion or "").casefold() != "ufc"
            )

        return {
            "feature_contract_version": self.catalog["feature_contract_version"],
            "active_v1_concept_count": len(active_v1_features(self.catalog)),
            "active_v1_name_count": len(self.all_v1_names),
            "elapsed_allowed_sources": list(self.catalog["elapsed_exposure_policy"]["allowed_sources"]),
            "cases": validations,
            "orientation_pair": [matchup.fighter_1_id, matchup.fighter_2_id],
            "interaction_count": len(matchup.interactions),
            "external_prior_fights_seen_in_fixture_cases": external_prior_count,
        }
