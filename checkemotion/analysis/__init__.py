"""emotion.analysis — call graph, metrics, and function narration."""

from .call_graph import (
    scan_directory, callers_of, callees_of,
    centrality, is_central, call_depth,
)
from .metrics import build_report, all_reports, FunctionReport
from .narrator import describe

__all__ = [
    "scan_directory", "callers_of", "callees_of",
    "centrality", "is_central", "call_depth",
    "build_report", "all_reports", "FunctionReport",
    "describe",
]
