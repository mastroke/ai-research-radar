from pathlib import Path

import pytest

from ai_research_radar.schedule import (
    ScheduleContext,
    ScheduleSettings,
    build_schedule_context,
    parse_schedule_settings,
    render_cron_line,
    render_systemd_units,
    render_telegram_poll_service,
)


def test_parse_schedule_settings_defaults() -> None:
    settings = parse_schedule_settings(None)

    assert settings == ScheduleSettings(preset="daily", at="08:00")


def test_parse_schedule_settings_rejects_unknown_preset() -> None:
    with pytest.raises(ValueError, match="Unknown schedule preset"):
        parse_schedule_settings("weekly")


def test_parse_schedule_settings_rejects_invalid_at() -> None:
    with pytest.raises(ValueError, match="HH:MM"):
        parse_schedule_settings("daily", at="25:99")


def test_render_daily_cron_line() -> None:
    context = ScheduleContext(
        config_path=Path("/etc/radar/radar.toml"),
        radar_command="/usr/bin/radar",
        working_directory=Path("/var/lib/radar"),
        settings=ScheduleSettings(preset="daily", at="07:30"),
        interval_seconds=86_400,
    )

    line = render_cron_line(context)

    assert line.startswith("30 7 * * *")
    assert "radar once --config /etc/radar/radar.toml" in line


def test_render_interval_cron_line_for_hourly() -> None:
    context = ScheduleContext(
        config_path=Path("/cfg/radar.toml"),
        radar_command="/usr/bin/radar",
        working_directory=Path("/cfg"),
        settings=ScheduleSettings(preset="interval", at="08:00"),
        interval_seconds=3_600,
    )

    assert render_cron_line(context) == (
        "0 * * * * cd /cfg && /usr/bin/radar once --config /cfg/radar.toml"
    )


def test_render_interval_cron_rejects_non_hourly_intervals() -> None:
    context = ScheduleContext(
        config_path=Path("/cfg/radar.toml"),
        radar_command="/usr/bin/radar",
        working_directory=Path("/cfg"),
        settings=ScheduleSettings(preset="interval", at="08:00"),
        interval_seconds=5_400,
    )

    with pytest.raises(ValueError, match="divisible by 3600"):
        render_cron_line(context)


def test_render_systemd_daily_timer() -> None:
    context = build_schedule_context(
        config_path=Path("/cfg/radar.toml"),
        interval_seconds=86_400,
        settings=ScheduleSettings(preset="daily", at="09:15"),
        working_directory=Path("/cfg"),
        radar_command="/usr/bin/radar",
    )

    service, timer = render_systemd_units(context)

    assert "Type=oneshot" in service
    assert "radar once --config" in service
    assert "OnCalendar=*-*-* 09:15:00" in timer
    assert "Persistent=true" in timer


def test_render_systemd_interval_timer() -> None:
    context = build_schedule_context(
        config_path=Path("/cfg/radar.toml"),
        interval_seconds=7_200,
        settings=ScheduleSettings(preset="interval", at="08:00"),
        radar_command="/usr/bin/radar",
    )

    _, timer = render_systemd_units(context)

    assert "OnUnitActiveSec=7200s" in timer


def test_render_telegram_poll_service() -> None:
    context = build_schedule_context(
        config_path=Path("/cfg/radar.toml"),
        interval_seconds=86_400,
        settings=ScheduleSettings(),
        radar_command="/usr/bin/radar",
    )

    service = render_telegram_poll_service(context)

    assert "Type=simple" in service
    assert "telegram poll --config" in service
    assert "Restart=on-failure" in service
