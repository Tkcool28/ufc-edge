#!/usr/bin/env python3
"""Exact/idempotent migration adding official UFC article families to raw source inventory."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "pipelines/audit_source_surfaces.py"

FUNCTION = '''\n\ndef add_ufc_official_articles(out: list[dict[str, Any]]) -> None:\n    base = ROOT / "ufc_official_articles"\n    if not base.exists():\n        return\n    for family in ("weigh_in", "scorecard"):\n        manifests = sorted(p for p in base.glob(f"*/{family}/manifest.json") if p.is_file())\n        manifest_path = latest(manifests)\n        if not manifest_path:\n            continue\n        m = load_json(manifest_path)\n        if m.get("complete_family_snapshot") is not True:\n            raise RuntimeError(f"Official UFC article family is not complete: {manifest_path}")\n        out.append({\n            "source": "ufc_official_content",\n            "collection": f"{family}_articles",\n            "snapshot": m.get("series_id") or manifest_path.parent.parent.name,\n            "manifest": manifest_path.as_posix(),\n            "rows": m.get("items"),\n            "attributes": ["raw_html"],\n            "status_counts": m.get("status_counts"),\n            "complete_family_snapshot": True,\n            "structured_parsing_requires_separate_audit": True,\n        })\n'''


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    if "def add_ufc_official_articles(" not in text:
        marker = "\ndef add_manifest_source(out: list[dict[str, Any]], source: str, glob_pattern: str) -> None:\n"
        if marker not in text:
            raise RuntimeError("source-surface function insertion target not found")
        text = text.replace(marker, FUNCTION + marker, 1)
    call = "    add_ufc_official_articles(items)\n"
    if call not in text:
        marker = "    add_ufc_resources(items)\n"
        if marker not in text:
            raise RuntimeError("source-surface main insertion target not found")
        text = text.replace(marker, marker + call, 1)
    PATH.write_text(text, encoding="utf-8")
    print("SOURCE_SURFACE_UFC_OFFICIAL_ARTICLES_MIGRATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
