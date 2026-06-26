import json
from pathlib import Path

import pytest

from ai_research_radar.brief import Finding
from ai_research_radar.cli import main
from ai_research_radar.memory import (
    FileMemoryStore,
    NullMemoryStore,
    dedup_findings,
    finding_key,
    open_memory_store,
)


def test_finding_key_normalizes_trailing_slash_and_case() -> None:
    assert finding_key("HTTPS://Example.com/item/") == finding_key("https://example.com/item")


def test_dedup_findings_keeps_last_entry_for_same_url() -> None:
    first = Finding(title="First", url="https://example.com/item", source="manual")
    second = Finding(
        title="Second",
        url="https://example.com/item/",
        source="arxiv",
        note="Updated note.",
    )

    deduped = dedup_findings([first, second])

    assert len(deduped) == 1
    assert deduped[0].title == "Second"
    assert deduped[0].note == "Updated note."


def test_null_memory_store_does_not_filter_seen_items() -> None:
    store = NullMemoryStore()
    findings = [Finding(title="Seed", url="https://example.com/seed", source="manual")]

    merged = store.merge_findings(findings)

    assert store.filter_unseen(merged) == merged
    store.mark_briefed(merged)
    assert store.filter_unseen(merged) == merged


def test_file_memory_store_persists_findings_and_seen_urls(tmp_path: Path) -> None:
    store_path = tmp_path / "memory.json"
    store = FileMemoryStore(store_path)
    first = Finding(title="Agent memory", url="https://example.com/memory", source="manual")
    second = Finding(title="Eval gates", url="https://example.com/eval", source="manual")

    store.merge_findings([first, second])
    store.mark_briefed([first])
    store.persist()

    reloaded = FileMemoryStore(store_path)

    assert {finding.url for finding in reloaded.merge_findings([])} == {
        "https://example.com/memory",
        "https://example.com/eval",
    }
    assert reloaded.filter_unseen(reloaded.merge_findings([])) == [
        Finding(title="Eval gates", url="https://example.com/eval", source="manual")
    ]


def test_open_memory_store_returns_null_store_when_disabled() -> None:
    store = open_memory_store(None)

    assert isinstance(store, NullMemoryStore)


def test_file_memory_store_rejects_invalid_payload(tmp_path: Path) -> None:
    store_path = tmp_path / "memory.json"
    store_path.write_text('{"version": 1, "findings": "bad"}', encoding="utf-8")

    with pytest.raises(ValueError, match="findings must be a list"):
        FileMemoryStore(store_path)


def test_once_skips_seen_items_on_second_run(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    memory_path = tmp_path / "memory.json"
    config_path = tmp_path / "radar.toml"
    config_path.write_text(
        f"""
title = "Desk Radar"
watch_terms = ["memory"]
memory_path = "{memory_path.as_posix()}"

[[items]]
title = "Agent memory"
url = "https://example.com/memory"
source = "manual"
note = "Tracks durable state."
""".strip(),
        encoding="utf-8",
    )

    first_exit = main(["once", "--config", str(config_path)])
    first_output = capsys.readouterr().out

    second_exit = main(["once", "--config", str(config_path)])
    second_output = capsys.readouterr().out

    assert first_exit == 0
    assert "Agent memory" in first_output
    assert second_exit == 0
    assert "No new items since the last brief" in second_output
    assert "Agent memory" not in second_output

    payload = json.loads(memory_path.read_text(encoding="utf-8"))
    assert payload["version"] == 1
    assert len(payload["findings"]) == 1
    assert payload["seen_urls"] == ["https://example.com/memory"]
