"""Shared UFC Edge feature-contract utilities."""

from .contract import (
    AUTHORITATIVE_FILES,
    ContractError,
    load_canonical_contract,
    load_feature_catalog,
    load_feature_schema,
    load_leakage_registry,
    materialized_feature_names,
    validate_catalog,
    validate_repository_contract,
)

__all__ = [
    "AUTHORITATIVE_FILES",
    "ContractError",
    "load_canonical_contract",
    "load_feature_catalog",
    "load_feature_schema",
    "load_leakage_registry",
    "materialized_feature_names",
    "validate_catalog",
    "validate_repository_contract",
]
