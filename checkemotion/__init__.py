"""emotion — assigns emotional personalities to Python functions.

Quick start
-----------
    from emotion import emotion

    @emotion
    def process_data(records):
        return [r for r in records if r.valid]

    process_data([...])    # prints emotion + description + per-call metrics

    from emotion import show_dashboard
    show_dashboard()       # rich terminal report for all registered functions

Public API
----------
  emotion         — decorator: emotion, profiling, and logging
  show_dashboard  — terminal dashboard (health, metrics, call graph)
  build_report    — FunctionReport for a single registered function
  all_reports     — list of FunctionReport for every registered function
  describe        — one-sentence description of any callable
  callers_of      — static call graph: which functions call this one
  callees_of      — static call graph: which functions this one calls
  scan_directory  — manually trigger call-graph scanning on a directory
  get_all_names   — list of all registered function names
  get_data        — raw registry dict for a function
"""

from .core.decorator       import emotion, flush_conversations
from .output.dashboard     import show_dashboard
from .output.conversation  import display_conversation
from .analysis.metrics     import build_report, all_reports, FunctionReport
from .analysis.narrator    import describe
from .analysis.call_graph  import callers_of, callees_of, scan_directory
from .core.registry        import get_all_names, get_data

__all__ = [
    "emotion",
    "flush_conversations",
    "show_dashboard",
    "display_conversation",
    "build_report",
    "all_reports",
    "FunctionReport",
    "describe",
    "callers_of",
    "callees_of",
    "scan_directory",
    "get_all_names",
    "get_data",
]
