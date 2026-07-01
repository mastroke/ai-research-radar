from __future__ import annotations

from pathlib import Path


def test_templates_exist() -> None:
    root = Path("templates")
    assert (root / "agency-sow-snippet.md").exists()
    assert (root / "procurement-one-pager.md").exists()


def test_gumroad_listing_exists() -> None:
    path = Path("docs/gumroad-listing.md")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "$49" in text
    assert "FAQ" in text


def test_sample_scenario_fixtures_exist() -> None:
    root = Path("scenarios/support-agent")
    assert (root / "scenarios.yaml").exists()
    assert (root / "fixtures/schemas/tools.json").exists()
    assert (root / "fixtures/prompts/system-billing.txt").exists()
