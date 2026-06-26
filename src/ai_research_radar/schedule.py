"""Scheduling presets for cron and systemd."""

from __future__ import annotations

import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

SCHEDULE_PRESETS = ("daily", "interval")
_TIME_PATTERN = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


@dataclass(frozen=True)
class ScheduleSettings:
    """Operator-facing schedule preset loaded from config or CLI flags."""

    preset: str = "daily"
    at: str = "08:00"


@dataclass(frozen=True)
class ScheduleContext:
    """Resolved paths and timing used to render scheduler templates."""

    config_path: Path
    radar_command: str
    working_directory: Path
    settings: ScheduleSettings
    interval_seconds: int


def resolve_radar_command() -> str:
    """Return an absolute radar invocation suitable for unit files."""

    radar_bin = shutil.which("radar")
    if radar_bin:
        return radar_bin
    return f"{Path(sys.executable).resolve()} -m ai_research_radar.cli"


def parse_schedule_settings(
    preset: str | None = None,
    *,
    at: str | None = None,
    default_preset: str = "daily",
    default_at: str = "08:00",
) -> ScheduleSettings:
    resolved_preset = (preset or default_preset).strip().lower()
    resolved_at = (at or default_at).strip()
    if resolved_preset not in SCHEDULE_PRESETS:
        allowed = ", ".join(SCHEDULE_PRESETS)
        raise ValueError(f"Unknown schedule preset {resolved_preset!r}. Expected one of: {allowed}")
    _parse_at_time(resolved_at)
    return ScheduleSettings(preset=resolved_preset, at=resolved_at)


def build_schedule_context(
    *,
    config_path: Path,
    interval_seconds: int,
    settings: ScheduleSettings,
    working_directory: Path | None = None,
    radar_command: str | None = None,
) -> ScheduleContext:
    resolved_config = config_path.resolve()
    resolved_workdir = (working_directory or resolved_config.parent).resolve()
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")

    return ScheduleContext(
        config_path=resolved_config,
        radar_command=radar_command or resolve_radar_command(),
        working_directory=resolved_workdir,
        settings=settings,
        interval_seconds=interval_seconds,
    )


def render_cron_line(context: ScheduleContext) -> str:
    """Render a single cron entry that runs `radar once`."""

    minute, hour = _cron_fields(context)
    command = (
        f"cd {context.working_directory} && "
        f"{context.radar_command} once --config {context.config_path}"
    )
    return f"{minute} {hour} * * * {command}"


def render_systemd_units(context: ScheduleContext) -> tuple[str, str]:
    """Render systemd service and timer unit bodies."""

    service = _render_systemd_service(context)
    timer = _render_systemd_timer(context)
    return service, timer


def render_telegram_poll_service(context: ScheduleContext) -> str:
    """Render a long-running systemd service for `radar telegram poll`."""

    lines = [
        "[Unit]",
        "Description=AI Research Radar Telegram control poll",
        "After=network-online.target",
        "Wants=network-online.target",
        "",
        "[Service]",
        "Type=simple",
        f"WorkingDirectory={context.working_directory}",
        (
            "ExecStart="
            f"{context.radar_command} telegram poll --config {context.config_path}"
        ),
        "Restart=on-failure",
        "RestartSec=30",
        "",
        "[Install]",
        "WantedBy=default.target",
    ]
    return "\n".join(lines) + "\n"


def _render_systemd_service(context: ScheduleContext) -> str:
    lines = [
        "[Unit]",
        "Description=AI Research Radar daily brief",
        "After=network-online.target",
        "Wants=network-online.target",
        "",
        "[Service]",
        "Type=oneshot",
        f"WorkingDirectory={context.working_directory}",
        (
            "ExecStart="
            f"{context.radar_command} once --config {context.config_path}"
        ),
        "",
        "[Install]",
        "WantedBy=timers.target",
    ]
    return "\n".join(lines) + "\n"


def _render_systemd_timer(context: ScheduleContext) -> str:
    timer_lines = [
        "[Unit]",
        "Description=AI Research Radar brief schedule",
        "",
        "[Timer]",
    ]
    if context.settings.preset == "daily":
        hour, minute = _parse_at_time(context.settings.at)
        timer_lines.append(f"OnCalendar=*-*-* {hour:02d}:{minute:02d}:00")
        timer_lines.append("Persistent=true")
    else:
        timer_lines.append("OnBootSec=5min")
        timer_lines.append(f"OnUnitActiveSec={context.interval_seconds}s")

    timer_lines.extend(
        [
            "",
            "[Install]",
            "WantedBy=timers.target",
        ]
    )
    return "\n".join(timer_lines) + "\n"


def _cron_fields(context: ScheduleContext) -> tuple[str, str]:
    if context.settings.preset == "daily":
        hour, minute = _parse_at_time(context.settings.at)
        return str(minute), str(hour)

    if context.interval_seconds % 3600 != 0:
        raise ValueError(
            "interval preset requires interval_seconds divisible by 3600 for cron; "
            "use systemd or set interval_seconds to a whole number of hours"
        )
    hours = context.interval_seconds // 3600
    if hours == 1:
        return "0", "*"
    if hours == 24:
        hour, minute = _parse_at_time(context.settings.at)
        return str(minute), str(hour)
    if 24 % hours != 0:
        raise ValueError(
            "interval preset cron supports hourly runs or divisors of 24 hours; "
            "use systemd for other intervals"
        )
    return "0", f"*/{hours}"


def _parse_at_time(value: str) -> tuple[int, int]:
    match = _TIME_PATTERN.match(value.strip())
    if not match:
        raise ValueError("schedule at must use HH:MM in 24-hour local time")
    hour = int(match.group(1))
    minute = int(match.group(2))
    return hour, minute
