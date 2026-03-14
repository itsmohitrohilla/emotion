from __future__ import annotations

import os
from typing import Literal, Optional

from ..core import registry
from ..schemas.emotions import EMOTIONS, RESET, BOLD, DIM
from ..utils.ansi import (
    health_color, complexity_color, bar,
    CYAN, GRAY, ORANGE, RED, YELLOW, GREEN,
)
from ..analysis.metrics import FunctionReport, all_reports


def render_report(report: FunctionReport, max_call_count: int, terminal_width: int) -> None:
    emotion_data          = EMOTIONS.get(report.emotion, EMOTIONS["content"])
    emoji                 = emotion_data.get("emoji", "❓")
    emotion_color         = emotion_data.get("color", "")
    health_value          = report.health_score()
    health_display_color  = health_color(health_value)
    complexity_display_color = complexity_color(report.cyclomatic_complexity)
    central_marker        = f"{YELLOW}★{RESET} " if report.is_central else "  "

    # ── Header ─────────────────────────────────────────────────────────────────
    print(
        f"{central_marker}{emotion_color}{BOLD}{emoji}  {report.name}{RESET}"
        f"  {DIM}[{report.emotion}]{RESET}"
        f"  {health_display_color}{report.star_rating()}  health={health_value:.0f}/100{RESET}"
    )

    # ── Description ────────────────────────────────────────────────────────────
    if report.description:
        max_description_length = terminal_width - 6
        display_description = report.description[:max_description_length]
        if len(report.description) > max_description_length:
            display_description = display_description[:-1] + "…"
        print(f"  {GRAY}↳ {display_description}{RESET}")

    # ── Static analysis ────────────────────────────────────────────────────────
    behavior_flags = []
    if report.has_recursion:  behavior_flags.append("recursive")
    if report.has_async:      behavior_flags.append("async")
    if report.has_try_except: behavior_flags.append("try/except")
    if report.has_yield:      behavior_flags.append("generator")
    behavior_flags_text = f"  {GRAY}[{', '.join(behavior_flags)}]{RESET}" if behavior_flags else ""

    print(
        f"  {GRAY}static  {RESET}"
        f"lines={BOLD}{report.line_count}{RESET}"
        f"  params={BOLD}{report.param_count}{RESET}"
        f"  branches={BOLD}{report.branch_count}{RESET}"
        f"  nesting={BOLD}{report.nesting_depth:.0f}{RESET}"
        f"  cc={complexity_display_color}{BOLD}{report.cyclomatic_complexity:.0f}{RESET} "
        f"{GRAY}({report.complexity_tier()}){RESET}"
        f"{behavior_flags_text}"
    )

    # ── Runtime metrics ────────────────────────────────────────────────────────
    call_count_bar        = bar(report.call_count, max_call_count)
    exception_percentage  = f"{report.exception_rate * 100:.0f}%"
    exception_display_color = (
        RED    if report.exception_rate > 0.1 else
        YELLOW if report.exception_rate > 0   else
        GREEN
    )

    print(
        f"  {GRAY}runtime {RESET}"
        f"calls={BOLD}{report.call_count}{RESET} {call_count_bar}"
        f"  errors={exception_display_color}{BOLD}{report.exception_count}{RESET}"
        f"{GRAY}({exception_percentage}){RESET}"
        f"  avg={BOLD}{report.average_time_ms:.1f}ms{RESET}"
        f"  total={GRAY}{report.total_time_ms:.0f}ms{RESET}"
    )

    # ── Profiling data (shown only if calls were profiled) ─────────────────────
    if report.average_wall_time_ms > 0 or report.peak_memory_kb > 0:
        memory_display_color = (
            RED    if report.peak_memory_kb > 10240 else
            YELLOW if report.peak_memory_kb > 1024  else
            GREEN
        )
        print(
            f"  {GRAY}profile {RESET}"
            f"wall={BOLD}{report.average_wall_time_ms:.1f}ms{RESET}"
            f"  cpu={BOLD}{report.average_cpu_time_ms:.2f}ms{RESET}"
            f"  mem_avg=+{BOLD}{report.average_memory_delta_kb:.1f}KB{RESET}"
            f"  mem_peak={memory_display_color}{BOLD}{report.peak_memory_kb:.1f}KB{RESET}"
        )

    # ── Call graph ─────────────────────────────────────────────────────────────
    if report.callers or report.callees:
        callers_display = ", ".join(report.callers[:5]) if report.callers else "—"
        callees_display = ", ".join(report.callees[:5]) if report.callees else "—"
        depth_display   = f"  depth={report.max_call_depth}" if report.max_call_depth > 0 else ""
        print(
            f"  {GRAY}graph   {RESET}"
            f"callers=[{CYAN}{callers_display}{RESET}]"
            f"  calls=[{CYAN}{callees_display}{RESET}]"
            f"{depth_display}"
        )

    # ── Social relationships ────────────────────────────────────────────────────
    if report.relationships:
        relationship_items = list(report.relationships.items())[:5]
        relationship_parts = [
            f"{ORANGE}{relationship_type}{RESET}→{other_name}"
            for other_name, relationship_type in relationship_items
        ]
        print(f"  {GRAY}social  {RESET}{', '.join(relationship_parts)}")

    print()


SortKey = Literal["call_count", "health", "complexity", "name"]


def show_dashboard(
    top_n:   Optional[int] = None,
    sort_by: SortKey        = "call_count",
) -> None:
    """Print a color-coded terminal dashboard for all registered functions."""
    reports = all_reports(sort_by=sort_by)
    if not reports:
        print(f"{DIM}No emotional functions registered yet.{RESET}")
        return

    if top_n:
        reports = reports[:top_n]

    try:
        terminal_width = min(os.get_terminal_size().columns, 120)
    except OSError:
        terminal_width = 120
    max_call_count = max((report.call_count for report in reports), default=1) or 1

    print(f"\n{BOLD}{'═' * terminal_width}{RESET}")
    print(f"{BOLD}  EMOTION AI  ·  FUNCTION DASHBOARD  ·  {len(reports)} function(s){RESET}")
    print(f"{BOLD}{'═' * terminal_width}{RESET}\n")

    for report in reports:
        render_report(report, max_call_count, terminal_width)

    # ── Summary footer ─────────────────────────────────────────────────────────
    total_call_count      = sum(report.call_count      for report in reports)
    total_exception_count = sum(report.exception_count for report in reports)
    overall_exception_rate = total_exception_count / total_call_count if total_call_count else 0.0
    average_health_score  = sum(report.health_score() for report in reports) / len(reports)

    print(f"{BOLD}{'─' * terminal_width}{RESET}")
    print(
        f"  {GRAY}TOTALS{RESET}"
        f"  functions={BOLD}{len(reports)}{RESET}"
        f"  calls={BOLD}{total_call_count}{RESET}"
        f"  errors={BOLD}{total_exception_count}{RESET}"
        f"{GRAY}({overall_exception_rate * 100:.1f}%){RESET}"
        f"  avg_health={health_color(average_health_score)}{BOLD}{average_health_score:.0f}/100{RESET}"
    )
    print(f"{BOLD}{'═' * terminal_width}{RESET}\n")
