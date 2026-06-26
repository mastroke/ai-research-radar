from pathlib import Path

from ai_research_radar.cli import main


def test_schedule_prints_daily_cron_line(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    config_path = tmp_path / "radar.toml"
    config_path.write_text(
        """
interval_seconds = 86400

[schedule]
preset = "daily"
at = "06:45"
""".strip(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "schedule",
            "--config",
            str(config_path),
            "--format",
            "cron",
        ]
    )

    output = capsys.readouterr().out.strip()

    assert exit_code == 0
    assert output.startswith("45 6 * * *")
    assert "radar once --config" in output


def test_schedule_writes_systemd_units(tmp_path: Path) -> None:
    config_path = tmp_path / "radar.toml"
    config_path.write_text(
        """
interval_seconds = 3600

[schedule]
preset = "interval"
""".strip(),
        encoding="utf-8",
    )
    output_dir = tmp_path / "units"

    exit_code = main(
        [
            "schedule",
            "--config",
            str(config_path),
            "--format",
            "systemd",
            "--output-dir",
            str(output_dir),
            "--with-telegram-poll",
        ]
    )

    assert exit_code == 0
    service = (output_dir / "radar-once.service").read_text(encoding="utf-8")
    timer = (output_dir / "radar-once.timer").read_text(encoding="utf-8")
    poll = (output_dir / "radar-telegram-poll.service").read_text(encoding="utf-8")

    assert "Type=oneshot" in service
    assert "OnUnitActiveSec=3600s" in timer
    assert "telegram poll" in poll
