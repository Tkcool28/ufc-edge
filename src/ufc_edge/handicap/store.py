from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

PACKET_SCHEMA_VERSION = "0.1.0"
GENERATOR_VERSION = "h00-0.1.0"
EXPECTED_DATA_CONTRACT = "0.4.0-draft"

CANONICAL_TABLES = (
    "fighters",
    "events",
    "fights",
    "fighter_round_stats",
    "fighter_round_position",
    "rankings",
    "fighter_profile_snapshots",
    "source_identity_links",
    "weigh_ins",
)

def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def normalize_lookup_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())

def parse_cutoff(value: str | datetime | date) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    else:
        text = str(value).strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            parsed = datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
        else:
            text = text.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

class CanonicalStore:
    """Read-only, schema-driven view over frozen canonical DATA."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root is not None else repository_root()
        self.canonical_dir = self.root / "data" / "canonical" / "v0"
        self.contract_path = self.root / "schemas" / "canonical_data_contract_v0.json"
        self.freeze_path = self.root / "provenance" / "data_phase_freeze_v0.json"
        self.manifest_path = self.canonical_dir / "manifest.json"

        self.contract = self._load_json(self.contract_path)
        self.freeze = self._load_json(self.freeze_path)
        self.manifest = self._load_json(self.manifest_path)
        self._validate_baseline()

        self.tables: dict[str, list[dict[str, Any]]] = {}
        self._indexes_ready = False

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _validate_baseline(self) -> None:
        contract_version = self.contract.get("contract_version")
        manifest_version = self.manifest.get("canonical_contract_version")
        freeze_version = self.freeze.get("canonical_contract_version")
        versions = {contract_version, manifest_version, freeze_version}
        if versions != {EXPECTED_DATA_CONTRACT}:
            raise RuntimeError(
                "H00 requires frozen DATA contract "
                f"{EXPECTED_DATA_CONTRACT}; observed {sorted(str(v) for v in versions)}"
            )
        frozen = {item["path"]: item["sha256"] for item in self.freeze.get("frozen_files", [])}
        expected_manifest_hash = frozen.get("data/canonical/v0/manifest.json")
        if not expected_manifest_hash:
            raise RuntimeError("DATA freeze does not bind the canonical manifest")
        actual_manifest_hash = sha256_file(self.manifest_path)
        if actual_manifest_hash != expected_manifest_hash:
            raise RuntimeError("canonical manifest no longer matches DATA freeze")
        for rel in (
            "schemas/canonical_data_contract_v0.json",
            "schemas/source_field_map_v0.json",
            "schemas/source_precedence_v0.json",
        ):
            expected = frozen.get(rel)
            if not expected or sha256_file(self.root / rel) != expected:
                raise RuntimeError(f"frozen DATA authority changed: {rel}")

    @property
    def manifest_sha256(self) -> str:
        frozen = {item["path"]: item["sha256"] for item in self.freeze.get("frozen_files", [])}
        return frozen["data/canonical/v0/manifest.json"]

    @property
    def freeze_sha256(self) -> str:
        return sha256_file(self.freeze_path)

    def _coerce(self, table: str, field: str, raw: str | None) -> Any:
        if raw is None or raw == "":
            return None
        spec = (
            self.contract.get("tables", {})
            .get(table, {})
            .get("fields", {})
            .get(field, {})
        )
        kind = spec.get("type")
        if kind == "integer":
            return int(raw)
        if kind == "number":
            return float(raw)
        if kind == "boolean":
            lowered = raw.strip().casefold()
            if lowered in {"true", "1"}:
                return True
            if lowered in {"false", "0"}:
                return False
            raise ValueError(f"invalid canonical boolean {table}.{field}={raw!r}")
        return raw

    def load_table(self, table: str) -> list[dict[str, Any]]:
        if table not in CANONICAL_TABLES:
            raise KeyError(f"unsupported canonical table: {table}")
        if table in self.tables:
            return self.tables[table]
        path = self.canonical_dir / f"{table}.csv"
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for raw_row in reader:
                rows.append(
                    {key: self._coerce(table, key, value) for key, value in raw_row.items()}
                )
        self.tables[table] = rows
        return rows

    def load_all(self) -> None:
        for table in CANONICAL_TABLES:
            self.load_table(table)
        self._build_indexes()

    def _build_indexes(self) -> None:
        if self._indexes_ready:
            return
        fighters = self.load_table("fighters")
        events = self.load_table("events")
        fights = self.load_table("fights")
        stats = self.load_table("fighter_round_stats")
        positions = self.load_table("fighter_round_position")
        rankings = self.load_table("rankings")
        profiles = self.load_table("fighter_profile_snapshots")
        links = self.load_table("source_identity_links")
        weigh_ins = self.load_table("weigh_ins")

        self.fighters_by_id = {row["fighter_id"]: row for row in fighters}
        self.events_by_id = {row["event_id"]: row for row in events}
        self.fights_by_id = {row["fight_id"]: row for row in fights}

        self.fights_by_fighter: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.fights_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in fights:
            self.fights_by_fighter[row["fighter_a_id"]].append(row)
            self.fights_by_fighter[row["fighter_b_id"]].append(row)
            self.fights_by_event[row["event_id"]].append(row)

        self.stats_by_fight_fighter: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in stats:
            self.stats_by_fight_fighter[(row["fight_id"], row["fighter_id"])].append(row)

        self.position_by_fight_fighter: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in positions:
            self.position_by_fight_fighter[(row["fight_id"], row["fighter_id"])].append(row)

        self.rankings_by_fighter: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rankings:
            self.rankings_by_fighter[row["fighter_id"]].append(row)

        self.profiles_by_fighter: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in profiles:
            self.profiles_by_fighter[row["fighter_id"]].append(row)

        self.links_by_fighter: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in links:
            if row.get("entity_type") == "fighter":
                self.links_by_fighter[row["canonical_id"]].append(row)

        self.weigh_ins_by_fight_fighter: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in weigh_ins:
            self.weigh_ins_by_fight_fighter[(row["fight_id"], row["fighter_id"])].append(row)

        self._indexes_ready = True

    def ensure_indexes(self) -> None:
        self.load_all()

    def canonical_name(self, fighter_id: str) -> str:
        self.ensure_indexes()
        row = self.fighters_by_id.get(fighter_id)
        if row is None:
            raise KeyError(f"unknown canonical fighter ID: {fighter_id}")
        return str(row["canonical_name"])

    def trusted_fighter_links(self, fighter_id: str) -> list[dict[str, Any]]:
        self.ensure_indexes()
        links = [
            row
            for row in self.links_by_fighter.get(fighter_id, [])
            if row.get("review_status") == "trusted"
        ]
        return sorted(
            links,
            key=lambda r: (
                str(r.get("source_name") or ""),
                str(r.get("source_id") or ""),
            ),
        )

    def trusted_aliases(self, fighter_id: str) -> list[str]:
        # Alias text may only come from already-trusted canonical identity-link columns.
        aliases: set[str] = set()
        for row in self.trusted_fighter_links(fighter_id):
            for field in ("alias", "source_alias", "source_display_name", "display_name"):
                value = row.get(field)
                if isinstance(value, str) and value.strip():
                    aliases.add(value.strip())
        canonical = self.canonical_name(fighter_id)
        aliases.discard(canonical)
        return sorted(aliases, key=lambda x: (normalize_lookup_text(x), x))

    def build_identity_lookup(self) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
        self.ensure_indexes()
        exact: dict[str, set[str]] = defaultdict(set)
        normalized: dict[str, set[str]] = defaultdict(set)
        for fighter_id, row in self.fighters_by_id.items():
            names = [str(row["canonical_name"]), *self.trusted_aliases(fighter_id)]
            for name in names:
                exact[name].add(fighter_id)
                normalized[normalize_lookup_text(name)].add(fighter_id)
        return exact, normalized

    def resolve_fighter(self, value: str) -> str:
        self.ensure_indexes()
        if value in self.fighters_by_id:
            return value
        exact, normalized = self.build_identity_lookup()
        if value in exact:
            candidates = sorted(exact[value])
            if len(candidates) == 1:
                return candidates[0]
            raise ValueError(self._ambiguity_message(value, candidates))
        norm = normalize_lookup_text(value)
        candidates = sorted(normalized.get(norm, set()))
        if len(candidates) == 1:
            return candidates[0]
        if candidates:
            raise ValueError(self._ambiguity_message(value, candidates))
        raise KeyError(f"unknown fighter name/ID: {value!r}; no fuzzy matching attempted")

    def _ambiguity_message(self, value: str, candidates: Iterable[str]) -> str:
        rendered = ", ".join(
            f"{fighter_id} ({self.canonical_name(fighter_id)})"
            for fighter_id in candidates
        )
        return f"ambiguous fighter lookup {value!r}; candidates: {rendered}"

    def metadata(self, cutoff: datetime, generated_at: datetime, generator_commit: str | None) -> dict[str, Any]:
        return {
            "packet_schema_version": PACKET_SCHEMA_VERSION,
            "generator_version": GENERATOR_VERSION,
            "generator_commit": generator_commit,
            "generated_at_utc": iso_utc(generated_at),
            "information_cutoff": iso_utc(cutoff),
            "data_contract_version": EXPECTED_DATA_CONTRACT,
            "canonical_manifest": {
                "path": "data/canonical/v0/manifest.json",
                "sha256": self.manifest_sha256,
            },
            "data_freeze": {
                "path": "provenance/data_phase_freeze_v0.json",
                "sha256": self.freeze_sha256,
            },
            "field_provenance": {
                "path": "data/canonical/v0/field_provenance.csv",
                "note": "Use canonical table primary keys/row keys to audit detailed field provenance.",
            },
        }
