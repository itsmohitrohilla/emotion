"""metrics.py — structured per-function report aggregating all data sources.

Combines:
  • 15-feature static vector        (core.analyzer)
  • Runtime counters                 (core.registry)
  • Profiling history                (core.registry profile_history)
  • Call graph                       (analysis.call_graph)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..core import registry
from .call_graph import callers_of, callees_of, centrality, is_central, call_depth


@dataclass
class FunctionReport:
    # Identity
    name:        str
    emotion:     str
    description: str

    # ── Static metrics (from the 15-feature vector) ───────────────────────────
    branch_count:          int   = 0
    line_count:            int   = 0
    param_count:           int   = 0
    cyclomatic_complexity: float = 0.0
    nesting_depth:         float = 0.0
    return_count:          int   = 0
    has_recursion:         bool  = False
    has_async:             bool  = False
    has_try_except:        bool  = False
    has_yield:             bool  = False

    # ── Runtime metrics ────────────────────────────────────────────────────────
    call_count:       int   = 0
    exception_count:  int   = 0
    exception_rate:   float = 0.0   # fraction in [0.0, 1.0]
    average_time_ms:  float = 0.0
    total_time_ms:    float = 0.0

    # ── Profiling averages (over the last ≤ 50 calls) ─────────────────────────
    average_wall_time_ms:    float = 0.0
    average_cpu_time_ms:     float = 0.0
    average_memory_delta_kb: float = 0.0
    peak_memory_kb:          float = 0.0

    # ── Call graph ─────────────────────────────────────────────────────────────
    callers:          List[str] = field(default_factory=list)
    callees:          List[str] = field(default_factory=list)
    centrality_score: int       = 0
    is_central:       bool      = False
    max_call_depth:   int       = 0

    # ── Social relationships ───────────────────────────────────────────────────
    relationships: Dict[str, str] = field(default_factory=dict)

    # ── Derived helpers ────────────────────────────────────────────────────────

    def complexity_tier(self) -> str:
        complexity_value = self.cyclomatic_complexity
        if complexity_value <= 2:   return "trivial"
        if complexity_value <= 5:   return "simple"
        if complexity_value <= 10:  return "moderate"
        if complexity_value <= 20:  return "complex"
        return "very complex"

    def size_tier(self) -> str:
        line_count_value = self.line_count
        if line_count_value <= 5:   return "tiny"
        if line_count_value <= 20:  return "small"
        if line_count_value <= 60:  return "medium"
        if line_count_value <= 150: return "large"
        return "huge"

    def health_score(self) -> float:
        """Composite 0–100 health score (higher = healthier)."""
        score = 100.0
        if self.exception_rate > 0.5:    score -= 40
        elif self.exception_rate > 0.2:  score -= 20
        elif self.exception_rate > 0.05: score -= 8
        if self.cyclomatic_complexity > 20:   score -= 25
        elif self.cyclomatic_complexity > 10: score -= 12
        elif self.cyclomatic_complexity > 6:  score -= 5
        if self.average_time_ms > 2000:  score -= 20
        elif self.average_time_ms > 500: score -= 10
        elif self.average_time_ms > 100: score -= 3
        if self.peak_memory_kb > 51200:  score -= 15
        elif self.peak_memory_kb > 10240: score -= 8
        return max(0.0, round(score, 1))

    def star_rating(self) -> str:
        health_value = self.health_score()
        if health_value >= 90: return "⭐⭐⭐⭐⭐"
        if health_value >= 75: return "⭐⭐⭐⭐"
        if health_value >= 55: return "⭐⭐⭐"
        if health_value >= 35: return "⭐⭐"
        return "⭐"


# ── Builder functions ─────────────────────────────────────────────────────────

def build_report(name: str) -> Optional[FunctionReport]:
    """Build a FunctionReport from all available data for *name*."""
    function_data = registry.get_data(name)
    if not function_data:
        return None

    features        = function_data.get("features", [0.0] * 15)
    call_count      = function_data.get("call_count", 0)
    exception_count = function_data.get("exception_count", 0)
    exception_rate  = exception_count / call_count if call_count > 0 else 0.0
    profile_history = function_data.get("profile_history", [])

    average_wall_time_ms    = (
        sum(entry["wall_time_ms"]    for entry in profile_history) / len(profile_history)
        if profile_history else 0.0
    )
    average_cpu_time_ms     = (
        sum(entry["cpu_time_ms"]     for entry in profile_history) / len(profile_history)
        if profile_history else 0.0
    )
    average_memory_delta_kb = (
        sum(entry["memory_delta_kb"] for entry in profile_history) / len(profile_history)
        if profile_history else 0.0
    )
    peak_memory_kb          = max(
        (entry["memory_peak_kb"] for entry in profile_history), default=0.0
    )

    centrality_value = centrality(name)
    caller_names     = callers_of(name)
    callee_names     = callees_of(name)
    depth_value      = call_depth(name)

    return FunctionReport(
        name        = name,
        emotion     = function_data.get("emotion", "content"),
        description = function_data.get("description", ""),

        branch_count          = int(features[0]),
        line_count            = int(features[1]),
        param_count           = int(features[2]),
        has_recursion         = bool(features[3]),
        has_async             = bool(features[4]),
        has_try_except        = bool(features[5]),
        has_yield             = bool(features[6]),
        cyclomatic_complexity = round(features[7], 1),
        nesting_depth         = round(features[8], 1),
        return_count          = int(features[9]),

        call_count      = call_count,
        exception_count = exception_count,
        exception_rate  = round(exception_rate, 3),
        average_time_ms = round(function_data.get("average_time_ms", 0.0), 2),
        total_time_ms   = round(function_data.get("total_time_ms", 0.0), 2),

        average_wall_time_ms    = round(average_wall_time_ms, 2),
        average_cpu_time_ms     = round(average_cpu_time_ms, 3),
        average_memory_delta_kb = round(average_memory_delta_kb, 2),
        peak_memory_kb          = round(peak_memory_kb, 2),

        callers          = caller_names,
        callees          = callee_names,
        centrality_score = centrality_value,
        is_central       = is_central(name),
        max_call_depth   = depth_value,

        relationships = function_data.get("relationships", {}),
    )


def all_reports(sort_by: str = "call_count") -> List[FunctionReport]:
    """Return a FunctionReport for every registered function, sorted."""
    all_names = registry.get_all_names()
    reports   = [report for report in (build_report(name) for name in all_names)
                 if report is not None]
    if sort_by == "call_count":
        reports.sort(key=lambda report: report.call_count, reverse=True)
    elif sort_by == "health":
        reports.sort(key=lambda report: report.health_score(), reverse=True)
    elif sort_by == "complexity":
        reports.sort(key=lambda report: report.cyclomatic_complexity, reverse=True)
    elif sort_by == "name":
        reports.sort(key=lambda report: report.name)
    return reports
